module.exports = {
	extends: [
		'@repo/eslint-config/index.js',
		'@electron-toolkit/eslint-config-ts/recommended',
		'@electron-toolkit/eslint-config-prettier'
	],
	rules: {
		'svelte/no-unused-svelte-ignore': 'off'
	}
};
