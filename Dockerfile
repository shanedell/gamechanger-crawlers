FROM --platform=linux/amd64 fedora:41

## running as root
USER root

## shell for RUN cmd purposes
SHELL ["/bin/bash", "-c"]

#####
## ## SYS Package Setup
#####

# LOCALE (important for python, etc.)
RUN dnf -y install glibc-locale-source glibc-langpack-en
RUN localedef -i en_US -f UTF-8 en_US.UTF-8

ENV LANG="en_US.UTF-8"
ENV LANGUAGE="en_US.UTF-8"
ENV LC_CTYPE="en_US.UTF-8"
ENV LC_NUMERIC="en_US.UTF-8"
ENV LC_TIME="en_US.UTF-8"
ENV LC_COLLATE="en_US.UTF-8"
ENV LC_MONETARY="en_US.UTF-8"
ENV LC_MESSAGES="en_US.UTF-8"
ENV LC_PAPER="en_US.UTF-8"
ENV LC_NAME="en_US.UTF-8"
ENV LC_ADDRESS="en_US.UTF-8"
ENV LC_TELEPHONE="en_US.UTF-8"
ENV LC_MEASUREMENT="en_US.UTF-8"
ENV LC_IDENTIFICATION="en_US.UTF-8"
ENV LC_ALL="en_US.UTF-8"

# Python3 and Env Prereqs
RUN dnf update -y \
    && dnf install -y \
   autoconf \
   automake \
   binutils \
   bison \
   flex \
   gcc \
   gcc-c++ \
   gettext \
   libtool \
   make \
   patch \
   pkgconfig \
   redhat-rpm-config \
   rpm-build \
   rpm-sign \
   byacc \
   cscope \
   ctags \
   diffstat \
   doxygen \
   elfutils \
   gcc-gfortran \
   git \
   indent \
   intltool \
   patchutils \
   rcs \
   subversion \
   swig \
   systemtap \
   libxml2 \ 
   libxslt \
    && dnf install -y \
        wget \
        python3.x86_64 \
        python3-devel.x86_64 \
        python3-pip.noarch \
        bzip2 \
        glibc.i686 \
        zip \
        unzip \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Update base python setup packages (avoids
RUN pip3 install --no-cache-dir --upgrade pip wheel setuptools

#####
## ## Chrome & ChromeDriver Setup
#####

## Installing AWS CLI
RUN curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install

## Getting chrome browser
RUN wget --no-check-certificate https://dl.google.com/linux/chrome/rpm/stable/x86_64/google-chrome-stable-120.0.6099.109-1.x86_64.rpm -P /tmp/ \
    && dnf install /tmp/google-chrome-stable-120.0.6099.109-1.x86_64.rpm -y \
    && rm /tmp/google-chrome-stable-120.0.6099.109-1.x86_64.rpm

## Getting chrome driver
RUN wget --no-check-certificate -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/120.0.6099.109/linux64/chromedriver-linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver-linux64/chromedriver -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ \
    && rm -rf /tmp/chromedriver*

#####
## ## Python packages
#####

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-py310_22.11.1-1-Linux-x86_64.sh && \
    bash Miniconda3-py310_22.11.1-1-Linux-x86_64.sh -b -p /opt/miniconda && \
    rm Miniconda3-py310_22.11.1-1-Linux-x86_64.sh

ENV PATH="${PATH}:/opt/miniconda/bin/"

# Create conda environment
RUN conda create -n gc-crawlers python=3.6 -y
RUN echo "source activate gc-crawlers" > ~/.bashrc

# Clone repo
RUN git clone https://github.com/dod-advana/gamechanger-crawlers.git

# Install Python dependencies
RUN /bin/bash -c "source activate gc-crawlers && \
                  pip install --upgrade pip setuptools wheel && \
                  pip install -r gamechanger-crawlers/docker/core/minimal-requirements.txt"