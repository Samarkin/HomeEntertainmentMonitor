while true;
do
	`dirname "$0"`/monitor-tv-apps.py
	echo Something went wrong. Restarting...
done
