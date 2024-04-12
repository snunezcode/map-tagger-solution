#Load Profile
version="$(curl https://version.code.ds.wwcs.aws.dev/?codeId=datop'&'moduleId=update)"
source $HOME/.bash_profile

#Clone Repository
cd /tmp
sudo rm -rf map-tagger-solution
git clone https://github.com/GitHubRepository/map-tagger-solution.git
cd map-tagger-solution
sudo cp -r server frontend /aws/apps

#React Application Installation
cd /aws/apps/frontend/; npm install; npm run build;

#Copy build content to www folder
cp -r /aws/apps/frontend/build/* /aws/apps/frontend/www/

#NodeJS API Core Installation
cd /aws/apps/server/; npm install;

#Re-Start API Services
cat /aws/apps/frontend/public/version.json
echo "Restarting the API Service..."
sleep 10
sudo service api.core restart

