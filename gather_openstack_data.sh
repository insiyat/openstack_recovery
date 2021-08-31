#!/bin/bash

#Author: Insiya Khandwala
 
# File Names
SECONDS=0
timestamp=$(date +"%Y-%m-%d_%H-%M")
blah=$(openstack region list -f value -c Region)
PORT=$(echo $blah.port_info.json)
NETWORKS=$(echo $blah.network_info.json)
SUBNETS=$(echo $blah.subnet_info.json)
SEGMENTS=$(echo $blah.segments_info.json)
PROJECTS=$(echo $blah.project_info.csv)
FLAVORS=$(echo $blah.flavors.json)
AGGREGATES=$(echo $blah.aggregate.json)
ROLES=$(echo $blah.role_assignment.json)
IMAGES=$(echo $blah.used_images.txt)
 
 
backup_files() {
   for filex in $PORT $NETWORKS $SUBNETS $PROJECTS $FLAVORS $AGGREGATES $ROLES;
   do
       if [ -f data/$filex ]; then
           echo "$filex already exist!, creating a backup $filex.$timestamp"
           mv data/$filex data/$filex.$timestamp
       fi
   done
}
# gathering functions
 
gather_ports () {
   openstack port list -c ID -c NAME  -c fixed_ips -c network_id -c project_id -c allowed_address_pairs -f json > data/$PORT
}
 
gather_networks () {
   echo "[" > data/$NETWORKS
   for x in $(openstack network list | egrep -v "+--|ID" | awk '{print $2}')
       do
           openstack network show $x -f json >> data/$NETWORKS
           echo "," >> data/$NETWORKS
       done
   sed -i '$ d'  data/$NETWORKS
   echo "]" >> data/$NETWORKS
 
   # Fix "True: to "True":
   sed -i 's/"True:/"True":/g' data/$NETWORKS
  
}
 
gather_subnets () {
   echo "[" > data/$SUBNETS
   for x in $(openstack subnet list | egrep -v "+--|ID" | awk '{print $2}')
       do
           openstack subnet show $x -f json >> data/$SUBNETS
           echo "," >> data/$SUBNETS
       done
   sed -i '$ d'  data/$SUBNETS
   echo "]" >> data/$SUBNETS
 
   # Fix "True: to "True":
   sed -i 's/"True:/"True":/g' data/$SUBNETS
}
 
gather_segments () {
   echo "[" > data/$SEGMENTS
   for x in $(openstack network segment list | egrep -v "+--|ID" | awk '{print $2}')
       do
           openstack network segment show $x -f json >> data/$SEGMENTS
           echo "," >> data/$SEGMENTS
       done
   sed -i '$ d'  data/$SEGMENTS
   echo "]" >> data/$SEGMENTS
  
   # Fix "True: to "True":
   sed -i 's/"True:/"True":/g' data/$SEGMENTS
}
 
gather_flavors () {
   echo "[" > data/$FLAVORS
   for x in $(openstack flavor list | egrep -v "+--|ID" | awk '{print $2}')
       do
           openstack flavor show $x -f json >> data/$FLAVORS
           echo "," >> data/$FLAVORS
       done
   sed -i '$ d'  data/$FLAVORS
   echo "]" >> data/$FLAVORS
}
 
gather_aggregates () {
   echo "[" > data/$AGGREGATES
   for x in $(openstack aggregate list | egrep -v "+--|ID" | awk '{print $2}')
       do
           openstack aggregate show $x -f json >> data/$AGGREGATES
           echo "," >> data/$AGGREGATES
       done
   sed -i '$ d'  data/$AGGREGATES
   echo "]" >> data/$AGGREGATES
}
 
gather_role_assignments () {
   openstack role assignment list --names -f json > data/$ROLES
}
 
gather_used_images () {
   openstack server list --all -c Image -f value | sort|uniq > data/$IMAGES
}
 
backup_files
gather_networks
gather_subnets
gather_segments
gather_ports
gather_flavors
gather_aggregates
gather_role_assignments
gather_used_images
 
 
openstack project list -f csv --long | grep -v "ID" > data/$PROJECTS
 
sed -i 's/"//g' data/$PROJECTS
 
for i in $(cat data/$PROJECTS)
do
   SEARCH=$(echo $i | awk -F',' '{print $1}')
   REPLACE=$(echo $i | awk -F',' '{print $2}')
 
   sed -i "s/$SEARCH/$REPLACE/g" data/$PORT
   sed -i "s/$SEARCH/$REPLACE/g" data/$NETWORKS
   sed -i "s/$SEARCH/$REPLACE/g" data/$SUBNETS
   sed -i "s/$SEARCH/$REPLACE/g" data/$SEGMENTS
done
 
duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."

