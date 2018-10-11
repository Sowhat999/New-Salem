# Salem Witch Trials Archive TEIP4 Migration Project

One-off migration script to convert TEI P4-encoded Salem Witchcraft Papers XML to Jekyll Markdown.

Use recursive clone to grab the TEI Stylesheet submodule repo also.

    git clone --recursive https://github.com/scholarslab/New-Salem.git

If you didn't do that and just did a clone, you have to initialize the submodule first or else it'll just stay an empty directory.

    cd Stylesheets
    git submodule init
    git submodule update

The TEI stylesheet scripts requite ant to build too, so you have to get that too.

After everything is set up, run the person re-keying script in pipenv shell to generate a new SWP xml with alpha-ordered person keys:

    python newnames.py

And then, finally, build the Pelican markdown files using:

    python build_salem.py

This will produce Pelican markdown output in `output/swp_new_id/pelican_md` and the tags.json tag-name map in `output/swp_new_id/tags`.
