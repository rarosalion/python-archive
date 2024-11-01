#!/bin/bash

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
WORK_DIR=`mktemp -d`
function cleanup {
    rm -fr "${WORK_DIR}"
}
trap cleanup EXIT #remove the temp directory



# Create contents to compress

pushd $WORK_DIR
echo Creating test data in $WORK_DIR

cat << EOF > 1
This is file number one
        This line is indented.
EOF

cat << EOF > 2
This is file #2
It has an emoji 😆!
EOF

mkdir 3

cat << EOF > 3/3.cn.txt
這是第三個檔。它包含漢字
EOF


# Create Compressed archives

echo 
echo Creating zip...
zip -r $SCRIPT_DIR/files/test_content.zip *

echo 
echo Creating tar.gz...
tar czvf $SCRIPT_DIR/files/test_content.tar.gz *

echo 
echo Creating 7z...
7z a $SCRIPT_DIR/files/test_content.7z *


# Done
popd