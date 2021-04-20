#!/bin/sh
export RUBYLIB="$SNAP/lib/ruby/snap:$SNAP/lib/ruby/snap/x86_64-linux:$RUBYLIB"
export GEM_PATH="$SNAP/lib/ruby/gems/snap:$GEM_PATH"

exec `dirname $0`/ruby.bare "$@"
