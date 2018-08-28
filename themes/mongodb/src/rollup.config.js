import babel from 'rollup-plugin-babel';
import commonjs from 'rollup-plugin-commonjs';
import {eslint} from 'rollup-plugin-eslint';
import {minify} from 'uglify-es';
import replace from 'rollup-plugin-replace';
import resolve from 'rollup-plugin-node-resolve';
import {uglify} from 'rollup-plugin-uglify';

export default {
    'plugins': [
        eslint({
            'exclude': 'node_modules/**',
            'throwOnError': true,
            'configFile': '.eslintrc.json'
        }),
        replace({
          'process.env.NODE_ENV': JSON.stringify('production')
        }),
        resolve(),
        commonjs({'include': 'node_modules/**'}),
        babel({exclude: 'node_modules/**'}),
        uglify({}, minify)
    ],
    'output': {'format': 'iife'}
};

