#!/bin/bash
MVN_VERSION=$(mvn -q \
    -Dexec.executable=echo \
    -Dexec.args='${project.version}' \
    --non-recursive \
    exec:exec)

FIJI_PATH="/home/ian/Fiji.app/jars/"
TARGET_PATH="/home/ian/Documents/Jython/FiberSight/target"
source "$HOME/.sdkman/bin/sdkman-init.sh"
sdk use java 8.0.382-tem
mvn clean package
ORIG_PACKAGE_PATH="$FIJI_PATH/FiberSight_beta-*.jar"
echo "Removing original package $ORIG_PACKAGE_PATH"
rm $ORIG_PACKAGE_PATH
echo "Copying path to $FIJI_PATH"
cp "$TARGET_PATH/FiberSight_beta-$MVN_VERSION.jar" $FIJI_PATH
