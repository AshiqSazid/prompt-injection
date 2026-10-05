"""`ots stamp` without the CLI (whose bitcoin.rpc import needs OpenSSL on Windows).

Mirrors otsclient.cmds.stamp_command: SHA-256 the file locally, append a random
nonce, hash again, submit only that digest to the default public calendars, and
write the detached .ots proof. The file itself never leaves the machine.
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
import os
import sys

from opentimestamps.calendar import RemoteCalendar
from opentimestamps.core.op import OpAppend, OpSHA256
from opentimestamps.core.serialize import StreamSerializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile

CALENDARS = [  # otsclient's defaults
    "https://a.pool.opentimestamps.org",
    "https://b.pool.opentimestamps.org",
    "https://a.pool.eternitywall.com",
    "https://ots.btc.catallaxy.com",
]
MIN_OK = 2

path = sys.argv[1]
out = path + ".ots"
if os.path.exists(out):
    sys.exit(f"{out} already exists; refusing to overwrite a proof")

with open(path, "rb") as fd:
    detached = DetachedTimestampFile.from_fd(OpSHA256(), fd)
print("file sha256:", detached.file_digest.hex())

nonce = detached.timestamp.ops.add(OpAppend(os.urandom(16)))
tip = nonce.ops.add(OpSHA256())

ok = []
for url in CALENDARS:
    try:
        tip.merge(RemoteCalendar(url).submit(tip.msg, timeout=20))
        ok.append(url)
        print("accepted by", url)
    except Exception as error:  # noqa: BLE001
        print("FAILED", url, type(error).__name__, error)

if len(ok) < MIN_OK:
    sys.exit(f"only {len(ok)} calendar(s) accepted; need {MIN_OK}; no proof written")

with open(out, "wb") as f:
    detached.serialize(StreamSerializationContext(f))
print(f"wrote {out}: {len(ok)} of {len(CALENDARS)} calendars")
