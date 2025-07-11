SHELL = '/bin/bash'

all: SOMParser.class

antlr.jar:
	wget -O antlr.jar https://www.antlr.org/download/antlr-4.7.2-complete.jar

SOMParser.java: antlr.jar SOM.g4
	java -cp antlr.jar org.antlr.v4.Tool SOM.g4

SOMParser.class: SOMParser.java
	javac -cp antlr.jar *.java

test: are-we-fast-yet SOMParser.class
	set -e; \
	find .. -path "../IntegrationTests" -prune -o -name '*.som' -print0 | while read -d $$'\0' i; do \
			echo "$${i}"; \
			OUT=`java -cp antlr.jar:. org.antlr.v4.gui.TestRig SOM classdef -diagnostics "$${i}" 2>&1`; \
			if [ ! -z "$$OUT" ]; then \
				echo "$$OUT"; \
				exit 1; \
			fi; \
	done

are-we-fast-yet:
	git clone --depth=1 https://github.com/smarr/are-we-fast-yet are-we-fast-yet

clean:
	rm *.java *.class *.tokens *.interp

clobber: clean
	rm antlr.jar
	rm -Rf are-we-fast-yet
