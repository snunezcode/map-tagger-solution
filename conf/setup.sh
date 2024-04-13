#!/bin/bash

cd /aws/apps/

#Verify code version
version="$(curl https://version.code.ds.wwcs.aws.dev/?codeId=maptagger'&'moduleId=deploy)"

#Install Software Packages
# Bug : https://github.com/amazonlinux/amazon-linux-2023/issues/397
while true; do
    echo "Trying to install app rpm packages ..."
    sudo yum install -y openssl nginx cronie && break
done

while true; do
    echo "Trying to install db rpm packages ..."
    sudo dnf install mariadb105-server -y && break
done


while true; do
    echo "Trying to install agent rpm packages ..."
    sudo yum install -y python3.11-pip && break
done

#Configure Agent Libraries
pip3.11 install boto3
pip3.11 install pymysql
 

#Configure database
sudo sh -c 'echo -e "\n[mysqld]\nskip-grant-tables\nskip-networking" >> /etc/my.cnf'
sudo systemctl start mariadb
sudo chkconfig mariadb on
cd /aws/apps/conf/; mysql --socket=/var/lib/mysql/mysql.sock < database.sql



#Create Certificates
sudo mkdir /etc/nginx/ssl/
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/server.key -out /etc/nginx/ssl/server.crt -subj "/C=US/ST=US/L=US/O=Global Security/OU=IT Department/CN=127.0.0.1"

#Copy Configurations
sudo cp conf/api.core.service /usr/lib/systemd/system/api.core.service
sudo cp conf/server.conf /etc/nginx/conf.d/

#Enable Auto-Start
sudo chkconfig nginx on
sudo chkconfig api.core on
sudo chkconfig crond on

#Change permissions
sudo chown -R ec2-user:ec2-user /aws/apps

#Copy aws-exports.json
cp /aws/apps/conf/aws-exports.json /aws/apps/frontend/public/
cp /aws/apps/conf/aws-exports.json /aws/apps/server/

#Re-Start NGINX Services
sudo service nginx restart

#NodeJS Installation
curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh --output install.sh
sh install.sh
. ~/.nvm/nvm.sh
nvm install 20.11.0


#NodeJS API Core Installation
cd /aws/apps/server/; npm install;

#Re-Start API Services
sudo service api.core restart

#React Application Installation
cd /aws/apps/frontend/; npm install; npm run build;


#Copy build content to www folder
cp -r /aws/apps/frontend/build/* /aws/apps/frontend/www/


#Agent scheduler
sudo service crond restart
crontab -l | { cat; echo "*/5 * * * * sh /aws/apps/agent/scheduler.sh"; } | crontab -

