for arg in "$@"
do
    pip uninstall arg
done

pip freeze > ./requirements.txt