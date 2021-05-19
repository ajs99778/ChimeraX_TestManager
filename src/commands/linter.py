import subprocess
import sys

from chimerax.core.commands import (
    CmdDesc, ListOf, StringArg, OpenFileNamesArg, register
)

def register_linter_command(logger):
    desc = CmdDesc(
        required=[("files", OpenFileNamesArg)],
        optional=[("linter", StringArg)],
        synopsis="run a linter on files",
    )
    
    register("linter", desc, linter)

def linter(session, files, linter="flake8"):
    for fname in files:
        session.logger.info("linting %s" % fname)

        args = [
            sys.executable,
            "-m", linter, fname,
        ]

        session.logger.info(" ".join(args))

        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

        out, err = proc.communicate()

        session.logger.info(
            "<pre>%s</pre>" % out.decode("utf-8"), is_html=True
        )
        session.logger.warning(
            "<pre>%s</pre>" % err.decode("utf-8"), is_html=True
        )
