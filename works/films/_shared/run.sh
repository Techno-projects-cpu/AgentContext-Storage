#!/bin/sh
# one entry point for the two English ads: skia stubs, ffmpeg, cinematic engine, shared art lib
export CF_ENGINE=/tmp/cs/cinematic-skill/skills/cinematic-film/scripts
export LD_LIBRARY_PATH=/tmp/gl
export PATH=/tmp/fbin:/tmp/venv/bin:$PATH
export PYTHONPATH=/home/user/AgentContext-Storage/works/films/_shared/eng:$PYTHONPATH
exec /tmp/venv/bin/python "$@"
