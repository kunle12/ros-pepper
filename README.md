# ros-pepper
## Getting started
Clone the repository into the home directory of your VM and navigate to the cloned directory.

```
git clone https://bitbucket.org/pepper_qut/ros-pepper ~/my_workspace
cd ~/my_workspace
```

## Building ROS
To build ROS simply run the build script. ***This process takes a long time!*** 

```
./build
```

*NOTE* A custom 4GB swapfile is needed to compile the existing ROS stack.
*NOTE* Need to manually install libyaml-cpp.a into /usr/lib directory.

To make use of your ROS installation, you now need to source the ROS setup.bash script.

```
source ~/my_workspace/ros_toolchain_install/setup.bash
```

Lastly, to copy the files to your robot, run the command:

```
pepper_deploy --core
```


## Building Additional Packages

If you wish to build additional ROS packages, you can now create a catkin workspace as usual (see the ROS documentation if you are unfamiliar with this process)

These packages can then be copied to the robot by running the commande:

```
pepper_deploy
```





