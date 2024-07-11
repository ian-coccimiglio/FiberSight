#!/bin/bash

FIJI_PATH="/home/ian/Fiji.app/jars/"
TARGET_PATH="/home/ian/Documents/Jython/FiberSight/target"
sdk use java 8.0.382-tem
mvn clean package
echo "Copying path to $FIJI_PATH"
cp "$TARGET_PATH/FiberSight_beta-0.1.0.jar" $FIJI_PATH
