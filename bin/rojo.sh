#!/bin/bash

function rojo() {
  SCRIPT=$(readlink -f "$BASH_SOURCE")
  SCRIPTPATH=$(dirname "$SCRIPT")

  chmod 775 "$SCRIPTPATH/rosh1.py"
  $SCRIPTPATH/rosh1.py $@ --private_rclt
}