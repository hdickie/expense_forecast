<?php

function ef_env($name, $default) {
    $value = getenv($name);
    if ($value === false || $value === '') {
        return $default;
    }
    return $value;
}

function ef_db_connection_string($superuser = false) {
    $user = $superuser ? ef_env('EF_DB_SUPERUSER', 'postgres') : ef_env('EF_DB_USER', 'virtuoso_user');
    $password = $superuser ? ef_env('EF_DB_SUPERUSER_PASSWORD', 'postgres') : ef_env('EF_DB_PASSWORD', 'virtuoso_password');

    return 'host=' . ef_env('EF_DB_HOST', 'host.docker.internal')
        . ' dbname=' . ef_env('EF_DB_NAME', 'postgres')
        . ' user=' . $user
        . ' password=' . $password
        . ' port=' . ef_env('EF_DB_PORT', '5433');
}

function ef_pg_connect($superuser = false) {
    return pg_connect(ef_db_connection_string($superuser));
}

function ef_cli_database_args() {
    return ' --database_hostname ' . escapeshellarg(ef_env('EF_DB_HOST', 'host.docker.internal'))
        . ' --database_name ' . escapeshellarg(ef_env('EF_DB_NAME', 'postgres'))
        . ' --database_username ' . escapeshellarg(ef_env('EF_DB_USER', 'virtuoso_user'))
        . ' --database_password ' . escapeshellarg(ef_env('EF_DB_PASSWORD', 'virtuoso_password'))
        . ' --database_port ' . escapeshellarg(ef_env('EF_DB_PORT', '5433')) . ' ';
}

?>
