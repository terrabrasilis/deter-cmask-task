# To build image for this dockerfile use this command:
#   docker build -t terrabrasilis/deter-cmask-data-task:vx.y.z -f env-scripts/Dockerfile --no-cache .
#
# To run without compose and without shell terminal use this command:
#   docker run -d --rm --name deter-cmask-script terrabrasilis/deter-cmask-data-task:vx.y.z
#   docker run -d --rm --name deter-cmask-script -v $PWD:/usr/local/data terrabrasilis/deter-cmask-data-task:vx.y.z
#
#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM ubuntu:20.04

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis" \
br.inpe.dpi.terrabrasilis="script-tasks" \
author="Andre Carvalho" \
author.email="andre.carvalho@inpe.br" \
description="Scripts for monthly get cmask data based on satellite images used to detect the DETER alerts."
#-------------Application Specific Stuff ----------------------------------------------------

RUN apt-get -o Acquire::ForceIPv4=true update \
    && DEBIAN_FRONTEND=noninteractive \
    TZ=America/Sao_Paulo \
    apt-get install -y \
    cron \
    python3-pip \
    postgis \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# define the timezone to run cron
ENV TZ=America/Sao_Paulo
# define the install path env var
ENV INSTALL_PATH /usr/local
# the data directory for put generated files 
ENV SHARED_DIR $INSTALL_PATH/data
# the scripts directory
ENV SCRIPT_DIR $INSTALL_PATH/scripts-shell

# create directories
RUN mkdir -p ${SHARED_DIR} \
    && mkdir -p ${SCRIPT_DIR}

# install python requirements
ADD env-scripts/requirements.txt $INSTALL_PATH/
RUN pip3 install -r $INSTALL_PATH/requirements.txt

# Install environment scripts
# ------------------------------------------------------
ADD env-scripts/exec_daily.sh $INSTALL_PATH/
ADD env-scripts/daily.cron /etc/cron.d/daily-cron
ADD env-scripts/docker-entrypoint.sh $INSTALL_PATH/bin/docker-entrypoint.sh

# Install main scripts
# ------------------------------------------------------
COPY scripts/ $SCRIPT_DIR/
RUN chmod +x $SCRIPT_DIR/*.sh \
    && chmod +x $INSTALL_PATH/*.sh \
    && chmod 0644 /etc/cron.d/daily-cron \
    && crontab -l | { cat; cat /etc/cron.d/daily-cron; } | crontab - \
    && chmod +x $INSTALL_PATH/bin/*.sh \
    && ln -s usr/local/bin/docker-entrypoint.sh / # backwards compat

# expose shared dir
VOLUME ["${SHARED_DIR}"]

ENTRYPOINT [ "/docker-entrypoint.sh" ]