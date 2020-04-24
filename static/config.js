(function() {
    var $configInput = $('#config-input');

    var defaultConfig = JSON.parse($configInput.val()) || (
        {
            default_destination: default_destination,
            upload_screenshots: true,
            upload_movies: true,
            url: '',
            title_settings: [],
            title_screenshots: [],
            title_movies: [],
            caption: '',
        }
    );

    var template = Ractive({
        target: '#tpl-root',
        template: '#tpl',
        data: {
            destinations: destinations,
            config: defaultConfig,
        },
        decorators: {
            hljs: function(node, renderSelector) {
                var renderNode = document.querySelector(renderSelector);
                renderNode.innerHTML = node.innerHTML;
                hljs.highlightBlock(renderNode);
                return {
                    teardown() {},
                    invalidate: () => {
                        renderNode.innerHTML = node.innerHTML;
                        hljs.highlightBlock(renderNode);
                        $configInput.val(JSON.stringify(this.get('config')));
                    }
                }
            }
        },
        addTitleSetting() {
            this.push('config.title_settings', {tid: '', destination: null});
        },
        deleteTitleSetting(index) {
            this.splice('config.title_settings', index, 1);
        },
        addTitleScreenshots() {
            this.push('config.title_screenshots', {tid: '', enabled: this.get('config.upload_screenshots')});
        },
        deleteTitleScreenshots(index) {
            this.splice('config.title_screenshots', index, 1);
        },
        addTitleMovies() {
            this.push('config.title_movies', {tid: '', enabled: this.get('config.upload_movies')});
        },
        deleteTitleMovies(index) {
            this.splice('config.title_movies', index, 1);
        },
    });
})();