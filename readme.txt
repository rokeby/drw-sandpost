readme / various useful commands

# error logs
cat /var/log/fw29/fw29_log.out.log
cat /var/log/fw29/fw29_log.err.log

# cronjob log
cat /var/log/syslog
cat /root/fw29/api.log

# edit cronjob
crontab -e

# cronjob
PATH=/root/fw29
HOME=/root/fw29
17 02 * * * /root/fw29/venv/bin/python3.12 /root/fw29/api.py >> api.log

# Enter virtual env
source env/bin/activate

# Secure copy to droplet
scp -r api.py root@64.23.140.231:/root/fw29
scp -r data root@64.23.140.231:/root/fw29

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