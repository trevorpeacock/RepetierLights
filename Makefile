
build:
	touch debian/test.deb
	aptly-build debian/
	mv debian/*.deb ./
