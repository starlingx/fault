SRCS = fmAPI.cpp fmFile.cpp fmLog.cpp fmMsgServer.cpp fmMutex.cpp fmSocket.cpp fmThread.cpp fmTime.cpp \
       fmAlarmUtils.cpp fmDb.cpp fmDbUtils.cpp fmDbAlarm.cpp fmSnmpUtils.cpp \
       fmDbEventLog.cpp fmEventSuppression.cpp fmConfig.cpp
CLI_SRCS = fm_cli.cpp
OBJS = $(SRCS:.cpp=.o)
CLI_OBJS = fm_cli.o
LDLIBS = -lstdc++ -lrt -luuid -lpq -lpthread -ljson-c
INCLUDES = -I./ -I$(shell pg_config --includedir)
CCFLAGS = -g -O2 -Wall -fPIC
EXTRACCFLAGS= -Wformat -Wformat-security

MAJOR ?= 1
MINOR ?= 0
OS_ID        = $(shell grep '^ID=' /etc/os-release | cut -f2- -d= | sed -e 's/\"//g')
OS_VERSION_ID= $(shell grep '^VERSION_ID=' /etc/os-release | cut -f2- -d= | sed -e 's/\"//g')
ifeq ($(OS_ID)-$(OS_VERSION_ID),centos-8)
LDLIBS += -lpython3.6m
INCLUDES += -I/usr/include/python3.6m
CCFLAGS += -Werror
else ifeq ($(OS_ID),debian)
LDLIBS += -lpython3.9
INCLUDES += -I/usr/include/python3.9
else
INCLUDES += -I/usr/include/python2.7
LDLIBS += -lpython2.7
endif


DESTDIR ?= /
BINDIR ?= /usr/local/bin
LIBDIR ?= /usr/local/lib64
INCDIR ?= /usr/local/include
CGCS_DOC_DEPLOY ?= /opt/deploy/cgcs_doc

LIBFMCOMMON_SO := libfmcommon.so
build: lib fmClientCli

.cpp.o:
	$(CXX) $(CCFLAGS) $(INCLUDES) $(EXTRACCFLAGS) -c $< -o $@

lib: $(OBJS)
	$(CXX) -Wl,-soname,$(LIBFMCOMMON_SO).$(MAJOR) -o $(LIBFMCOMMON_SO).$(MAJOR).$(MINOR) -shared $(OBJS) $(EXTRAARFLAGS) ${LDLIBS}
	ln -sf $(LIBFMCOMMON_SO).$(MAJOR).$(MINOR) $(LIBFMCOMMON_SO).$(MAJOR)
	ln -sf $(LIBFMCOMMON_SO).$(MAJOR).$(MINOR) $(LIBFMCOMMON_SO)

fmClientCli: $(CLI_OBJS) lib
	$(CXX) -o $@ $(CLI_OBJS) -L./ -lfmcommon

clean:
	@rm -f $(OBJ) *.o *.so fmClientCli

install:
	install -m 755 -d $(DESTDIR)$(BINDIR)
	install -m 755 -d $(DESTDIR)$(LIBDIR)
	install -m 755 -d $(DESTDIR)$(INCDIR)
	install -m 755 -d $(DESTDIR)$(CGCS_DOC_DEPLOY)
	install -m 755 fmClientCli $(DESTDIR)$(BINDIR)
	install -m 755 fm_db_sync_event_suppression.py $(DESTDIR)$(BINDIR)
	install -m 755 fm_log.py $(DESTDIR)$(BINDIR)
	install -m 644 fmDbAPI.h $(DESTDIR)$(INCDIR)
	install -m 644 fmAPI.h $(DESTDIR)$(INCDIR)
	install -m 644 fmThread.h $(DESTDIR)$(INCDIR)
	install -m 644 fmAlarm.h $(DESTDIR)$(INCDIR)
	install -m 644 fmConfig.h $(DESTDIR)$(INCDIR)
	install -m 644 fmLog.h $(DESTDIR)$(INCDIR)
	install -m 644 fmAlarm.h $(DESTDIR)$(CGCS_DOC_DEPLOY)
	install -m 755 $(LIBFMCOMMON_SO).$(MAJOR).$(MINOR) $(DESTDIR)$(LIBDIR)
	ln -sf $(LIBFMCOMMON_SO).$(MAJOR).$(MINOR) $(DESTDIR)$(LIBDIR)/$(LIBFMCOMMON_SO).$(MAJOR)
	ln -sf $(LIBFMCOMMON_SO).$(MAJOR).$(MINOR) $(DESTDIR)$(LIBDIR)/$(LIBFMCOMMON_SO)
