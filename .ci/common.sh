export WORKON_HOME=~/.virtualenvs

[ -e /usr/local/bin/virtualenvwrapper.sh ] && {
	. /usr/local/bin/virtualenvwrapper.sh;
	workon iris-api
}
