#!/usr/bin/env bash

# Usage:
#   pylint.sh <path/to/python/dir/or/files>

# Fail on error
set -e

CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "${CURR_DIR}/../common/base.sh"

PYLINT_CMD="pylint"

# Function to check if pylint is installed
function check_pylint() {
	if ! command -v ${PYLINT_CMD} &>/dev/null; then
		error "Command \"${PYLINT_CMD}\" not found."
		error "Please make sure pylint is installed and check your PATH settings."
		error "For Debian/Ubuntu, you can run the following command:"
		error "  sudo pip3 install --upgrade --no-cache-dir pylint"
		exit 1
	fi
}

# Function to run pylint on given files
function pylint_run() {
	${PYLINT_CMD} "$@"
}

function find_py_srcs() {
  find "$@" -type f -name "*.py"
}

# Function to process files or directories
function run_pylint() {
	for target in "$@"; do
		if [[ -f "${target}" ]]; then
			if py_ext "${target}"; then
				pylint_run "${target}"
				info "Done formatting ${target}"
			else
				warning "Do nothing. ${target} is not a Python file."
			fi
		else
			local srcs
			srcs="$(find_py_srcs "${target}")"
			if [[ -z "${srcs}" ]]; then
				warning "Do nothing. No Python files found under ${target}."
				continue
			fi
			pylint_run ${srcs}
			ok "Done formatting Python files under ${target}"
		fi
	done
}

# Main function to execute script logic
function main() {
	check_pylint

	if [[ "$#" -eq 0 ]]; then
		error "Usage: $0 <path/to/python/dirs/or/files>"
		exit 1
	fi

	run_pylint "$@"
}

main "$@"
