#!/bin/sh
unclutter -idle 0 &
matchbox-window-manager -use_titlebar no &
exec surf -F /home/ark/index.html
