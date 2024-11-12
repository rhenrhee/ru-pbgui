import streamlit as st
from time import sleep
import json
from pathlib import Path, PurePath
from datetime import datetime
import glob
import ansible_runner
import re
import getpass
import shutil
import socket

PBGDIR = Path.cwd()

class VPS:
    def __init__(self):
        self._hostname = None
        self.path = None
        self.privat_data_dir = None
        self.ip = None
        self.root_pw = None
        self.initial_root_pw = None
        self.user = getpass.getuser()
        self.user_pw = None
        self.swap = "2.5G"
        self.last_init = None
        self.last_setup = None
        self.last_update = None
        self.init_status = None
        self.setup_status = None
        self.update_status = None
        self.command = "unknown"
        self.command_text = "unknown"
        self.reboot = False
        self.init_log = ""
        self.setup_log = ""
        self.update_log = ""
        self.bucket = None
        self.coinmarketcap_api_key = None
        self.firewall = True
        self.firewall_ssh_port = 22
        self.firewall_ssh_ips = ""

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, new_hostanme):
        self._hostname = new_hostanme
        self.path = Path(f'{PBGDIR}/data/vpsmanager/hosts/{self.hostname}')

    def load(self):
        with open(self.path, 'r') as f:
            config = json.load(f)
            if "_hostname" in config:
                self._hostname = config["_hostname"]
            if "ip" in config:
                self.ip = config["ip"]
            if "user" in config:
                self.user = config["user"]
            if "swap" in config:
                self.swap = config["swap"]
            if "last_setup" in config:
                self.last_setup = config["last_setup"]
            if "last_init" in config:
                self.last_init = config["last_init"]
            if "last_update" in config:
                self.last_update = config["last_update"]
            if "setup_status" in config:
                self.setup_status = config["setup_status"]
            if "init_status" in config:
                self.init_status = config["init_status"]
            if "update_status" in config:
                self.update_status = config["update_status"]
            if "firewall" in config:
                self.firewall = config["firewall"]
            if "firewall_ssh_port" in config:
                self.firewall_ssh_port = config["firewall_ssh_port"]
            if "firewall_ssh_ips" in config:
                self.firewall_ssh_ips = config["firewall_ssh_ips"]
            if "command" in config:
                self.command = config["command"]
            if "command_text" in config:
                self.command_text = config["command_text"]

    def is_vps_in_hosts(self):
        # open /etc/hosts and check if the ip and hostname is in there
        hosts = Path('/etc/hosts')
        if hosts.exists():
            with open(hosts, 'r') as f:
                for line in f:
                    found = re.search(f'^{self.ip}[ \t]+{self.hostname}$', line)
                    if found:
                        return True
        return False
    
    def is_vps_ssh_open(self):
        if not self.ip:
            return False
        # Test if ssh port open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set timeout to 0.5s
        sock.settimeout(0.5)
        result = sock.connect_ex((self.ip, 22))
        if result == 0:
            return True
        else:
            return False
    
    def has_init_parameters(self):
        if self.ip and self.root_pw and self.initial_root_pw and self.user and self.user_pw:
            return True
        else:
            return False
    
    def has_setup_parameters(self):
        if self.hostname and self.user and self.user_pw and self.swap and self.bucket and self.coinmarketcap_api_key:
            return True
        else:
            return False
    
    def has_user_pw(self):
        if self.user_pw:
            return True
        else:
            return False

    def is_initialized(self):
        if self.init_status == "successful":
            return True
        else:
            return False

    @st.fragment(run_every=1)
    def view_init_status(self):
        st.text(f'Init Status: {self.init_status}')

    @st.fragment(run_every=1)
    def view_setup_status(self):
        st.text(f'Setup Status: {self.setup_status}')
    
    @st.fragment(run_every=1)
    def view_update_status(self):
        st.text(f'Update Status: {self.update_status}')

    @st.fragment(run_every=1)
    def view_init_log(self):
        ansi = self.init_log
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        result = ansi_escape.sub("", ansi)
        st.code(result, language="coffeescript")

    @st.fragment(run_every=1)
    def view_setup_log(self):
        ansi = self.setup_log
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        result = ansi_escape.sub("", ansi)
        st.code(result, language="coffeescript")
    
    @st.fragment(run_every=1)
    def view_update_log(self):
        ansi = self.update_log
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        result = ansi_escape.sub("", ansi)
        st.code(result, language="coffeescript")

    def init_event_handler(self, event):
        log = Path(f'{self.path}/vps_init.log')
        if (dump := event.get("stdout")):
            with open(log, "a") as logfile:
                logfile.write(dump)
            self.init_log = self.init_log + dump
    
    def setup_event_handler(self, event):
        log = Path(f'{self.path}/vps_setup.log')
        if (dump := event.get("stdout")):
            with open(log, "a") as logfile:
                logfile.write(dump)
            self.setup_log = self.setup_log + dump
    
    def update_event_handler(self, event):
        log = Path(f'{self.path}/vps_update.log')
        if (dump := event.get("stdout")):
            with open(log, "a") as logfile:
                logfile.write(dump)
            self.update_log = self.update_log + dump

    def remove_init_log(self):
        log = Path(f'{self.path}/vps_init.log')
        if log.exists():
            log.unlink()
    
    def remove_setup_log(self):
        log = Path(f'{self.path}/vps_setup.log')
        if log.exists():
            log.unlink()
    
    def remove_update_log(self):
        log = Path(f'{self.path}/vps_update.log')
        if log.exists():
            log.unlink()

    def init_status_handler(self, status_data, runner_config):
        self.init_status = status_data["status"]

    def setup_status_handler(self, status_data, runner_config):
        self.setup_status = status_data["status"]
    
    def update_status_handler(self, status_data, runner_config):
        self.update_status = status_data["status"]

    def init_finished(self, runner_config=None):
        self.last_init = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save()
        shutil.rmtree(f'{self.path}/tmp', ignore_errors=True)

    def setup_finished(self, runner_config=None):
        self.last_setup = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save()
        shutil.rmtree(f'{self.path}/tmp', ignore_errors=True)
    
    def update_finished(self, runner_config=None):
        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save()
        shutil.rmtree(f'{self.path}/tmp', ignore_errors=True)

    def save(self):
        if self.hostname:
            self.path = Path(f'{PBGDIR}/data/vpsmanager/hosts/{self.hostname}')
            self.path.mkdir(parents=True, exist_ok=True)
            self.privat_data_dir = Path(f'{self.path}/tmp')
            self.privat_data_dir.mkdir(parents=True, exist_ok=True)
            file = f'{self.path}/{self.hostname}.json'
            config = {
                "_hostname": self.hostname,
                "ip": self.ip,
                "user": self.user,
                "swap": self.swap,
                "bucket": self.bucket,
                "coinmarketcap_api_key": self.coinmarketcap_api_key,
                "last_setup": self.last_setup,
                "last_init": self.last_init,
                "last_update": self.last_update,
                "setup_status": self.setup_status,
                "init_status": self.init_status,
                "update_status": self.update_status,
                "firewall": self.firewall,
                "firewall_ssh_port": self.firewall_ssh_port,
                "firewall_ssh_ips": self.firewall_ssh_ips,
                "command": self.command,
                "command_text": self.command_text
            }
            with open(file, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=4)
    
    def delete(self):
        vps_path = Path(f'{PBGDIR}/data/vpsmanager/hosts/{self.hostname}')
        shutil.rmtree(vps_path, ignore_errors=True)
    
class VPSManager:
    def __init__(self):
        self.vpss = []
        self.path = Path(f'{PBGDIR}/data/vpsmanager/hosts')
        self.find_vps()
    
    def list(self):
        return list(map(lambda x: x.hostname, self.vpss))

    def find_vps_by_hostname(self, hostname):
        for vps in self.vpss:
            if vps.hostname == hostname:
                return vps
        return None

    def find_vps(self):
        p = str(Path(f'{PBGDIR}/data/vpsmanager/hosts/*/*.json'))
        hosts = glob.glob(p, recursive=False)
        if hosts:
            for host in hosts:
                v = VPS()
                v.path = Path(host)
                v.load()
                self.vpss.append(v)
        # sort vpss by hostname
        self.vpss.sort(key=lambda x: x.hostname)

    def add_vps(self):
        return VPS()

    def init_vps(self, vps : VPS, debug = False):
        vps.setup_status = None
        vps.save()
        vps.remove_init_log()
        vps.init_log = ""
        if debug:
            tags = "debug,all"
        else:
            tags = None
        ansible_runner.run_async(
            playbook=str(PurePath(f'{PBGDIR}/vps-init.yml')),
            inventory=vps.hostname,
            extravars={
                'hostname': vps.hostname,
                'ip': vps.ip,
                'initial_root_pw': vps.initial_root_pw,
                'root_pw': vps.root_pw,
                'user': vps.user,
                'user_pw': vps.user_pw,
                'debug': debug
            },
            quiet=True,
            tags=tags,
            verbosity=1,
            private_data_dir=vps.privat_data_dir,
            event_handler=vps.init_event_handler,
            status_handler=vps.init_status_handler,
            finished_callback=vps.init_finished
        )
    
    def setup_vps(self, vps : VPS, debug = False):
        vps.save()
        vps.remove_setup_log()
        vps.setup_log = ""
        if debug:
            tags = "debug,all"
        else:
            tags = None
        ansible_runner.run_async(
            playbook=str(PurePath(f'{PBGDIR}/vps-setup.yml')),
            inventory=vps.hostname,
            extravars={
            'hostname': vps.hostname,
            'user': vps.user,
            'user_pw': vps.user_pw,
            'swap_size': vps.swap,
            'bucket': vps.bucket,
            'coinmarketcap_api_key': vps.coinmarketcap_api_key,
            'firewall': vps.firewall,
            'firewall_ssh_port': vps.firewall_ssh_port,
            'firewall_ssh_ips': vps.firewall_ssh_ips.split(','),
            'debug': debug
            },
            quiet=True,
            tags=tags,
            verbosity=1,
            private_data_dir=vps.privat_data_dir,
            event_handler=vps.setup_event_handler,
            status_handler=vps.setup_status_handler,
            finished_callback=vps.setup_finished
        )

    def update_vps(self, vps : VPS, debug = False):
        vps.update_status = None
        vps.save()
        vps.remove_update_log()
        vps.update_log = ""
        if debug:
            tags = "debug,all"
        else:
            tags = None
        ansible_runner.run_async(
            playbook=str(PurePath(f'{PBGDIR}/{vps.command}.yml')),
            inventory=vps.hostname,
            extravars={
                'hostname': vps.hostname,
                'user': vps.user,
                'user_pw': vps.user_pw,
                'firewall': vps.firewall,
                'firewall_ssh_port': vps.firewall_ssh_port,
                'firewall_ssh_ips': vps.firewall_ssh_ips.split(','),
                'reboot': vps.reboot,
                'debug': debug
            },
            quiet=True,
            tags=tags,
            verbosity=1,
            private_data_dir=vps.privat_data_dir,
            event_handler=vps.update_event_handler,
            status_handler=vps.update_status_handler,
            finished_callback=vps.update_finished
        )

def main():
    print("Don't Run this Class from CLI")

if __name__ == '__main__':
    main()
