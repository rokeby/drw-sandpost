readme / useful commands / drw-sandpost

# droplet error logs
cat /var/log/drw-sandpost/sandpost_log.out.log
cat /var/log/drw-sandpost/sandpost_log.err.log

# cronjob log
cat /var/log/syslog
cat /root/drw-sandpost/api.log

# edit cronjob
crontab -e

# cronjob
PATH=/root/drw-sandpost
HOME=/root/drw-sandpost
17 02 * * * /root/drw-sandpost/venv/bin/python3.12 /root/drw-sandpost/api.py >> api.log

# Enter virtual env
source env/bin/activate

# Secure copy to droplet
scp -r api.py root@64.23.140.231:/root/drw-sandpost
scp -r data root@64.23.140.231:/root/drw-sandpost

# Reloading droplet
sudo supervisorctl reload
sudo systemctl restart nginx

# Droplet IP
http://64.23.140.231/ 

# An affirmation that you exist

# gunicorn bind app
gunicorn --bind=0.0.0.0 api:app
gunicorn -w 3 api:app

# install requirements
pip install -r requirements.txt

# make requirements.txt
pip freeze > requirements.txt