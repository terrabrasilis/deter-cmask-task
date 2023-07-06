
#!/bin/bash

countDownloadedFiles(){
    BASE_DIR="${1}"
    TRY_FOUND=(${BASE_DIR}/*${2}*.tif)
    FOUNDED_FILES=0
    if [ -f ${TRY_FOUND[0]} ]; then
        FOUNDED_FILES=`ls ${BASE_DIR}/*${2}*.tif |wc -l`
    fi;
    echo "${FOUNDED_FILES}"
}