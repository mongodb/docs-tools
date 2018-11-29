import babel from 'rollup-plugin-babel';
import commonjs from 'rollup-plugin-commonjs';
import {eslint} from 'rollup-plugin-eslint';
import json from 'rollup-plugin-json';
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
        resolve({
            'browser': true,
            'exclude': 'node_modules/**',
            'preferBuiltins': false
        }),
        commonjs({'include': 'node_modules/**'}),
        json(),
        babel({
            'exclude': 'node_modules/**',
            'presets': [
                [
                    'env',
                    {
                        'modules': false,
                        'targets': {'browsers': 'defaults, IE >= 10'}
                    }
                ]
            ],
            'plugins': [
                'external-helpers',
                'babel-plugin-transform-object-rest-spread',
                'babel-plugin-transform-for-of-as-array',
                ['babel-plugin-transform-es2015-for-of', {'loose': true}],
                ['transform-react-jsx', {'pragma': 'preact.h'}]
            ]

        }),
        uglify({}, minify)
    ],
    'output': {'format': 'iife'}
};

