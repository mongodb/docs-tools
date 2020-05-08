const SLIDE_ANIMATION_TIME_MS = 400;
let $currentPage = $('.sidebar a.current');

function isVisible(target) {
    return target.hasClass('current');
}

function handleTocSectionVisibility() {
    // Show/hide the appropriate TOC sections
    const $sidebar = $('.sphinxsidebarwrapper');
    const $visibleRootSection = $('ul.toc-section-root.current');
    const $nonvisibleRootSections = $('ul.toc-section-root:not(.current)');
    const $visibleNestedSection = $('ul.toc-section-nested.current');
    const $nonvisibleNestedSections = $('ul.toc-section-nested:not(.current)');
    $visibleRootSection.show();
    $visibleNestedSection.show();
    $nonvisibleRootSections.hide();
    $nonvisibleNestedSections.hide();
    $sidebar.show();
}
function handleRootSectionNavigation(e) {
    e.preventDefault();
    const $targetSection = $(e.currentTarget).parent();

    function collapseSection(section) {
        const $sectionHeading = section.children('h3');
        const $sectionContent = section.children(':not(h3)');

        $sectionHeading.removeClass('open');
        $sectionContent.stop().slideUp(SLIDE_ANIMATION_TIME_MS, () => {
            section.add(section.children()).removeClass('current');
        });
    }

    function expandSection(section) {
        section.add(section.children()).addClass('current');
        section.children('ul.toc-section-root').stop().
            slideDown(SLIDE_ANIMATION_TIME_MS);
    }

    if (isVisible($targetSection)) {
        collapseSection($targetSection);
    } else {
        const $visibleSection = $('li.toctree-l1.current');
        collapseSection($visibleSection);
        expandSection($targetSection);
    }
}

function handleSectionNavigation(e) {
    e.preventDefault();
    const $targetHeading = $(e.currentTarget);
    const $targetSection = $targetHeading.parent();

    function collapseSection(section) {
        const $sectionHeading = section.children('h4, h5');
        const $sectionContent = section.children(':not(h4, h5)');

        $sectionHeading.removeClass('open');
        $sectionContent.stop().slideUp(SLIDE_ANIMATION_TIME_MS, () => {
            section.add(section.children()).removeClass('current');
        });
    }

    function expandSection(section) {
        const $sectionHeading = section.children('h4, h5');
        const $sectionContent = section.children(':not(h4, h5)');

        $sectionHeading.addClass('open current');
        $sectionContent.stop().slideDown(SLIDE_ANIMATION_TIME_MS, () => {
            section.addClass('current');
            $sectionContent.addClass('current');
        });
    }

    if (isVisible($targetSection)) {
        collapseSection($targetSection);
    } else {
        expandSection($targetSection);
    }
}

function handleCompositePage(e) {
    e.preventDefault();
    const $targetIcon = $(e.currentTarget);
    const $targetPage = $targetIcon.parent();
    const $subpageSection = $targetPage.siblings('ul.toc-section-nested');

    const isClosed = $targetIcon.hasClass('is-closed');
    if (isClosed) {
        $subpageSection.stop().slideDown();
        $targetIcon.removeClass('is-closed');
        $targetIcon.addClass('is-open');
    } else {
        $subpageSection.stop().slideUp();
        $targetIcon.removeClass('is-open');
        $targetIcon.addClass('is-closed');
    }
}


function addNavigationHandlers() {
    // Handle TOC navigation
    const $tocSections = $('.toctree-root .toctree-l1');
    $tocSections.on('click', 'h3', handleRootSectionNavigation);
    $tocSections.on('click', 'h4', handleSectionNavigation);
    $tocSections.on('click', 'h5', handleSectionNavigation);
    $tocSections.on('click', 'a span.nested-page-toggle', handleCompositePage);
}

function addIcons() {
    // Add the page icon (file-alt-regular) to (expand-icon)
    const $tocPagesWithoutChildren = $(
        'ul.toctree-root li:not(.contains-nested) > a.reference'
    );
    $tocPagesWithoutChildren.prepend(() =>
        $('<span class="page-icon"></span>')
    );

    // Add composite page toggles
    const closedPageToggleIcon =
    '<span class="nested-page-toggle is-closed"></span>';
    const openPageToggleIcon =
    '<span class="nested-page-toggle is-open contains-current-page"></span>';

    const $closedPagesWithChildren = $('li.contains-nested > a:not(.current)').
        filter($('li.contains-nested > ul:not(.toc-section-nested.current)').siblings('a'));
    const $openPagesWithChildren = $('li.contains-nested > a.current').
        add($('li.contains-nested > ul.toc-section-nested.current').siblings('a'));

    $closedPagesWithChildren.prepend(closedPageToggleIcon);
    $openPagesWithChildren.prepend(openPageToggleIcon);

    // Add a vertical line to nested sub-pages
    const $nestedTocPages = $('ul.toc-section-nested a.reference');
    $nestedTocPages.prepend(() => $('<span class="nested-page-line"></span>'));
}

export function setup() {
    const project = $('body').attr('data-project');
    const isStitch = project === 'stitch' || project === 'realm';
    if (isStitch) {
        $currentPage = $('.sidebar a.current');
        $currentPage.parent('li').addClass('selected-item');

        handleTocSectionVisibility();
        addNavigationHandlers();
        addIcons();
    }
}
