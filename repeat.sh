LOCATION=/afs/cs.unc.edu/home/saba/public_html/COMP_classes
rm $LOCATION/maintenance_needed
while :
do
    if ! python3 gather_data.py; then
        notify-send 'COMP_classes script failed. Please check.'
	touch $LOCATION/maintenance_needed
        break
    else
        sleep 60
	if test -f $LOCATION/stop_loop; then
	    rm $LOCATION/stop_loop
	    break
	fi
    fi
done
