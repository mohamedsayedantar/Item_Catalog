# Item_Catalog
a web application provide several categories each category contain its own items,
visitors can see all items and each category items and also can see each item description,
authenticated users can add items or edit or delete their own items only,
this web application uses google 3rd party authentication to authenticate the users.


## run
the database currently contain several categories with three items only as examples,
for case you want modify this database and make your own, first download the project and follow these steps.
   1. delete `categories.db` file
   2. from your terminal run `database_create.py` file using `python database_create.py`
   3. modify what ever you want in the `lotsofcategories.py` file then run this file using `python lotsofcategories.py`
   4. run the application using `python project.py` visit the website on `http://localhost:5000/`
   

## The virtual machine
  This project makes use of the same Linux-based virtual machine (VM) to install the virtual machine:-
  1. Install VirtualBox from https://www.virtualbox.org/wiki/Download_Old_Builds_5_1
  2. Install Vagrant from https://www.vagrantup.com/downloads.html
  3. Download the VM configuration from https://s3.amazonaws.com/video.udacity-data.com/topher/2018/April/5acfbfa3_fsnd-virtual-machine/fsnd-virtual-machine.zip
  4. use your terminal and go to the directory called vagrant using `cd`
  5. Start the virtual machine using `vagrant up` command
  6. you can run `vagrant ssh` to log in to your newly installed Linux VM
  
  Note: in case error importing simplejson using the VM run in your terminal `sudo apt-get install python-simplejson`
