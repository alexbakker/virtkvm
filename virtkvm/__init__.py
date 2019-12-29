import argparse
import hmac
import io
import json
import subprocess
import time
import traceback
from typing import List, Tuple

import flask
import libvirt
import xmltodict
import yaml
from flask import Flask, request

class LibvirtConfig:
    def __init__(self, data: dict):
        self.uri: str = data["uri"]
        self.domain: str = data["domain"]

class HTTPConfig:
    def __init__(self, data: dict):
        ipv = int(data.get("ipversion", 4))
        if ipv == 6:
            addr = data["address"][1:].split(']:')
        else:
            addr = data["address"].split(":")
        self.host: str = addr[0]
        self.port: int = int(addr[1])
        self._security = data["security"]

    @property
    def is_secure(self) -> bool:
        return self._security["enabled"]

    @property
    def secret(self) -> str:
        return self._security["secret"]

class CommandsConfig:
    def __init__(self, data: dict):
        self.host_commands: List[str] = data.get("host", [])
        self.guest_commands: List[str] = data.get("guest", [])

class Config:
    def __init__(self, data: dict):
        self.http = HTTPConfig(data["http"])
        self.devices = [(d["vendor"], d["product"]) for d in data["devices"]]
        self.displays = data["displays"]
        self.libvirt = LibvirtConfig(data["libvirt"])
        self.commands = CommandsConfig(data.get("commands", {}))

    @staticmethod
    def load(filename: str):
        with io.open(filename) as f:
            return Config(yaml.safe_load(f))

class Virt:
    def __init__(self, uri: str, domain: str):
        self._con = libvirt.open(uri)
        self._dom = self._con.lookupByName(domain)

    def get_devices(self) -> List[dict]:
        devs = []

        desc = xmltodict.parse(self._dom.XMLDesc())
        for dev in desc["domain"]["devices"]["hostdev"]:
            if dev["@type"] == "usb":
                devs.append(dev)

        return devs

    @staticmethod
    def get_device_ids(desc: dict) -> Tuple[int, int]:
        return (int(desc["source"]["vendor"]["@id"], 16),
                int(desc["source"]["product"]["@id"], 16))

    def get_device_by_ids(self, ids: Tuple[int, int]) -> dict:
        for dev in self.get_devices():
            if self.get_device_ids(dev) == ids:
                return dev

        return None

    def attach_devices(self, devs: List[dict]):
        for ids in devs:
            dev = self.get_device_by_ids(ids)
            if dev is None:
                dev = xmltodict.unparse({
                    "hostdev": {
                        "@mode": "subsystem",
                        "@type": "usb",
                        "source": {
                            "vendor": {"@id": hex(ids[0])},
                            "product": {"@id": hex(ids[1])}
                        }
                    }
                })
                self._dom.attachDevice(dev)

    def detach_devices(self, devs: List[dict]):
        for dev in self.get_devices():
            if self.get_device_ids(dev) in devs:
                xml = xmltodict.unparse({"hostdev": dev})
                self._dom.detachDevice(xml)

class Switch:
    def __init__(self, config: Config):
        self.config = config
        self.virt = Virt(config.libvirt.uri, config.libvirt.domain)

    @staticmethod
    def _call_dccutil(display: dict, ident: int):
        return subprocess.call([
            "ddcutil",
            "--bus", str(display["bus"]),
            "setvcp", hex(display["feature"]), hex(ident)
        ])

    @staticmethod
    def _call_commands(command: str):
        return subprocess.call(command, shell=True)

    def switch_to_host(self):
        for display in self.config.displays:
            self._call_dccutil(display, display["host"])
        for command in self.config.commands.host_commands:
            self._call_commands(command)
        self.virt.detach_devices(self.config.devices)

    def switch_to_guest(self):
        for display in self.config.displays:
            self._call_dccutil(display, display["guest"])
        for command in self.config.commands.guest_commands:
            self._call_commands(command)
        self.virt.attach_devices(self.config.devices)

switch: Switch = None
app = Flask(__name__)

@app.route("/switch", methods=["POST"])
def app_switch():
    if switch.config.http.is_secure:
        secret = request.headers.get("X-Secret")
        if secret is None \
           or not hmac.compare_digest(switch.config.http.secret, secret):
            flask.abort(403)

    cases = {
        "host": switch.switch_to_host,
        "guest": switch.switch_to_guest
    }

    if not request.json \
       or not "to" in request.json \
       or not request.json["to"] in cases:
        flask.abort(400)

    error = None
    try:
        cases[request.json["to"]]()
    except:
        error = traceback.format_exc()

    return flask.jsonify({"success": True, "error": error})

def main():
    parser = argparse.ArgumentParser(description="The poor man's KVM switch for libvirt and VFIO users", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", dest="config", required=True, help="the YAML configuration file")
    args = parser.parse_args()

    global switch
    config = Config.load(args.config)
    switch = Switch(config)

    app.run(host=config.http.host, port=config.http.port)
