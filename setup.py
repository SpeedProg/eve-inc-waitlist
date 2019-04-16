import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="EVE Incursion waitlist",
    version="1.6.3",
    author="SpeedProg",
    author_email="speedprogde@googlemail.com",
    description="Waitlist geared towards EveOnline Incursion Groups",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SpeedProg/eve-inc-waitlist",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points="""
    [console_scripts]
    waitlist = waitlist.entry:main
    [babel.extractors]
    waitlist_themes = waitlist.utility.babel.themes_extractor:extract
    """
)

