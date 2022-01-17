while :
do
	if ! python3 gather_data.py; then
        notify-send 'COMP_classes script failed. Please check.'
        break
    else
        sleep 300
    fi
done
