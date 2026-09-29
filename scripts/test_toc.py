"""Build into a temporary directory and check the TOC in headless Chrome."""
import functools
import http.server
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "themes/ZedPaper"
BROWSER = Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"

header_source = (THEME / "layouts/_partials/header.html").read_text(encoding="utf-8")
panel_css_source = (THEME / "assets/css/extended/floating-panel.css").read_text(encoding="utf-8")
toc_css_source = (THEME / "assets/css/extended/toc.css").read_text(encoding="utf-8")
panel_js_source = (THEME / "assets/js/floating-panel.js").read_text(encoding="utf-8")
toc_js_source = (THEME / "assets/js/floating-toc.js").read_text(encoding="utf-8")
assert 'id="toc-trigger"' not in header_source, "TOC trigger remains in header.html"
assert "@media (min-width: 1001px)" in panel_css_source and "width: 240px" in panel_css_source, "Shared panel CSS does not own the responsive sidebar"
assert "floating-panel-dialog" not in toc_css_source, "TOC CSS still owns shared dialog styling"
assert "showModal" in panel_js_source and "matchMedia" in panel_js_source, "Shared panel controller does not own dialog/responsive behavior"
assert all(token not in toc_js_source for token in ("showModal", "matchMedia", ".close()")), "TOC controller still owns shared panel behavior"

CHECKS = r'''<!doctype html><html><body><img src="/hold" hidden><iframe id="page" style="width:390px;height:844px;border:0"></iframe>
<script>
const frame = document.getElementById('page');
const pause = (milliseconds = 150) => new Promise(resolve => setTimeout(resolve, milliseconds));
function check(value, message) { if (!value) throw new Error(message); }
function load(path) { return new Promise(resolve => { frame.onload = resolve; frame.src = path; }); }
function loadScript(path) { return new Promise((resolve, reject) => { const script = document.createElement('script'); script.src = path; script.onload = resolve; script.onerror = reject; document.head.append(script); }); }
function resolveColor(doc, win, value) {
  const sample = doc.createElement('span');
  sample.style.color = value;
  doc.body.append(sample);
  const color = win.getComputedStyle(sample).color;
  sample.remove();
  return color;
}
function findStyleRules(ruleList, selector) {
  const matches = [];
  for (const rule of ruleList) {
    if (rule.selectorText?.includes(selector)) matches.push(rule);
    if (rule.cssRules) matches.push(...findStyleRules(rule.cssRules, selector));
  }
  return matches;
}
(async () => {
  try {
    await load('/posts/20260805hello-world/');
    const doc = frame.contentDocument, win = frame.contentWindow;
    const panel = doc.querySelector('.floating-panel[data-panel-id="toc"]');
    check(panel, 'TOC is not rendered through the shared floating panel');
    const trigger = panel.querySelector('#toc-trigger');
    const dialog = panel.querySelector('#toc-dialog');
    const sidebar = panel.querySelector('#toc-sidebar');
    const contentHost = panel.querySelector('.floating-panel-content');
    const topLink = doc.getElementById('top-link');
    const progress = topLink?.querySelector('.reading-progress');
    const progressArrow = topLink?.querySelector('.progress-arrow');
    const inlineCode = doc.querySelector('.post-content p code');
    const codeBlock = doc.querySelector('.post-content pre > code');
    const copyButton = doc.querySelector('.post-content .copy-code');
    const unorderedListItem = doc.querySelector('.post-content ul > li');
    const orderedListItem = doc.querySelector('.post-content ol > li');
    const singleCover = doc.querySelector('.post-header > .entry-cover-single');
    const singleCoverLink = singleCover?.querySelector('.entry-cover-link');
    const postTitle = doc.querySelector('.post-header .post-title');
    check(trigger && dialog && sidebar && contentHost, 'Shared TOC panel structure is incomplete');
    check(!doc.querySelector('.header #toc-trigger'), 'TOC trigger remains coupled to the site header');
    check(new Set([trigger.id, dialog.id, sidebar.id]).size === 3, 'Floating panel IDs are not unique');
    check(topLink && progress, 'Missing reading progress control');
    check(progressArrow, 'Missing rounded progress arrow');
    check(inlineCode && codeBlock, 'Missing code samples');
    check(unorderedListItem && orderedListItem, 'Missing ordered or unordered list samples');
    const secondaryColor = resolveColor(doc, win, 'var(--secondary)');
    check(win.getComputedStyle(unorderedListItem, '::marker').color === secondaryColor, 'Unordered-list marker does not use secondary');
    check(win.getComputedStyle(orderedListItem, '::marker').color === secondaryColor, 'Ordered-list marker does not use secondary');
    check(win.getComputedStyle(unorderedListItem).color !== secondaryColor && win.getComputedStyle(orderedListItem).color !== secondaryColor, 'List marker color leaked into list text');
    check(singleCover?.querySelector('img') && singleCoverLink && postTitle, 'Post single cover structure is incomplete');
    check(Boolean(singleCover.compareDocumentPosition(postTitle) & win.Node.DOCUMENT_POSITION_FOLLOWING), 'Post single cover is not above the title');
    check(singleCoverLink.href === 'https://images.example.test/manhattan' && singleCoverLink.target === '_blank' && singleCoverLink.rel.includes('noopener'), 'Post single cover does not link safely to its source');
    const isMonospaceFamily = value => /consolas|monospace/i.test(value);
    check(isMonospaceFamily(win.getComputedStyle(inlineCode).fontFamily) && isMonospaceFamily(win.getComputedStyle(codeBlock).fontFamily), 'Code does not use a monospace font family');
    const codeFontRules = Array.from(doc.styleSheets).flatMap(sheet => {
      try { return findStyleRules(sheet.cssRules, 'code').filter(rule => isMonospaceFamily(rule.style.fontFamily)); }
      catch { return []; }
    });
    check(codeFontRules.some(rule => rule.selectorText.split(',').some(selector => selector.trim() === 'code')) && codeFontRules.some(rule => rule.selectorText.split(',').some(selector => selector.trim() === 'pre')), 'Code font family is not explicitly set to a monospace family');
    check(copyButton, 'Missing code copy button');
    check(win.getComputedStyle(copyButton).display !== 'none' && win.getComputedStyle(copyButton).visibility === 'visible', 'Code copy button is hidden without hover');
    check(win.getComputedStyle(topLink).visibility === 'visible', 'Post progress control is not always visible');
    check(progress.textContent === '0%', 'Reading progress does not start at 0%');
    check(win.getComputedStyle(progress).opacity === '1' && win.getComputedStyle(progressArrow).opacity === '0', 'Progress and arrow initial visibility is wrong');
    check(win.getComputedStyle(progress).transitionDuration === '0.2s', 'Progress fade duration is not 200ms');
    const hoverProgressRules = Array.from(doc.styleSheets).flatMap(sheet => {
      try { return findStyleRules(sheet.cssRules, '.top-link:hover .reading-progress'); }
      catch { return []; }
    });
    check(hoverProgressRules.length > 0 && hoverProgressRules.every(rule => rule.parentRule?.conditionText?.includes('hover: hover')), 'Touch devices can retain the progress button hover state');
    check(progressArrow.querySelector('path').getAttribute('stroke-linecap') === 'round' && progressArrow.querySelector('path').getAttribute('stroke-linejoin') === 'round', 'Progress arrow is not rounded');
    topLink.focus();
    await pause(250);
    check(win.getComputedStyle(progress).opacity === '0' && win.getComputedStyle(progressArrow).opacity === '1', 'Focused progress control does not reveal the arrow');
    topLink.blur();
    await pause(250);
    const maxScroll = doc.documentElement.scrollHeight - win.innerHeight;
    win.scrollTo(0, maxScroll / 2);
    await pause();
    check(Math.abs(parseInt(progress.textContent, 10) - 50) <= 1, 'Reading progress does not update near 50%');
    win.scrollTo(0, 0);
    await pause();
    check(win.getComputedStyle(trigger).display !== 'none' && !trigger.hidden, 'Mobile button hidden');
    check(win.getComputedStyle(trigger).position === 'fixed', 'Narrow-screen TOC button is not fixed');
    const triggerRect = trigger.getBoundingClientRect();
    const topLinkRect = topLink.getBoundingClientRect();
    check(triggerRect.bottom < topLinkRect.top, 'TOC button is not above progress control');
    check(Math.abs(triggerRect.width - topLinkRect.width) < 1 && Math.abs(triggerRect.height - topLinkRect.height) < 1, 'Floating controls do not share a size');
    check(doc.documentElement.scrollWidth <= win.innerWidth, 'Mobile horizontal overflow');
    trigger.click();
    check(dialog.open, 'Button did not open dialog');
    const openingStyle = win.getComputedStyle(dialog);
    check(openingStyle.animationName === 'floating-panel-dialog-in' && openingStyle.animationDuration === '0.2s', 'Dialog does not use the shared 200ms opening animation');
    check(dialog.contains(doc.activeElement), 'Focus did not enter dialog');
    check(!dialog.querySelector('details, summary'), 'TOC remains collapsible');
    check(!dialog.querySelector('.toc-title'), 'Dialog content retains a TOC-specific panel title');
    await pause(250);
    const rect = dialog.getBoundingClientRect();
    check(Math.abs(rect.left + rect.width / 2 - win.innerWidth / 2) < 2, 'Dialog not horizontally centered');
    check(Math.abs(rect.top + rect.height / 2 - win.innerHeight / 2) < 2, 'Dialog not vertically centered');
    const dialogBody = dialog.querySelector('.floating-panel-dialog-body');
    check(contentHost.parentElement === dialogBody, 'Mobile layout did not move the original content host into the dialog');
    const tocInner = dialog.querySelector('.toc .inner');
    const tocLink = tocInner.querySelector('a[href^="#"]');
    const innerStyle = win.getComputedStyle(tocInner);
    check(Array.from(tocInner.querySelectorAll('ul')).every(list => win.getComputedStyle(list).listStyleType === 'none'), 'TOC list markers remain visible');
    check(parseFloat(innerStyle.paddingLeft) >= 12 && parseFloat(innerStyle.paddingRight) >= 12, 'TOC content padding is missing');
    check(win.getComputedStyle(tocLink).display === 'block', 'TOC heading is not a full-row link');
    const linkRect = tocLink.getBoundingClientRect();
    const rowEdgeTarget = doc.elementFromPoint(linkRect.right - 2, linkRect.top + linkRect.height / 2);
    check(rowEdgeTarget?.closest('a') === tocLink, 'TOC row edge is not clickable');
    const dialogLinks = Array.from(tocInner.querySelectorAll('a[href^="#"]'));
    const dialogSegments = Array.from(tocInner.querySelectorAll('.toc-section-progress'));
    const activeDialogLinks = dialogLinks.filter(link => link.classList.contains('is-active'));
    check(activeDialogLinks.length > 0, 'Dialog TOC has no active headings');
    const firstActiveIndex = dialogLinks.indexOf(activeDialogLinks[0]);
    const activeLinkRect = activeDialogLinks[0].getBoundingClientRect();
    const activeSegmentRect = dialogSegments[firstActiveIndex].getBoundingClientRect();
    check(Math.abs(activeSegmentRect.top - activeLinkRect.top - 2) < 1 && Math.abs(activeSegmentRect.height - Math.max(3, activeLinkRect.height - 4)) < 1, `Dialog TOC progress segment is not aligned with its heading: segment=${activeSegmentRect.top}/${activeSegmentRect.height}, link=${activeLinkRect.top}/${activeLinkRect.height}`);
    check(dialogSegments[firstActiveIndex].querySelector('.toc-section-progress-fill').getBoundingClientRect().height > 0, 'Dialog TOC active progress fill is empty');
    const dialogActiveFrame = tocInner.querySelector('.toc-active-frame');
    const dialogLastActiveRect = activeDialogLinks.at(-1).getBoundingClientRect();
    const dialogFrameRect = dialogActiveFrame.getBoundingClientRect();
    check(win.getComputedStyle(dialogActiveFrame).opacity === '1' && Math.abs(dialogFrameRect.top - activeLinkRect.top) < 1 && Math.abs(dialogFrameRect.height - (dialogLastActiveRect.bottom - activeLinkRect.top)) < 1, 'Dialog TOC active frame does not cover the active headings');
    const extra = doc.createElement('div');
    extra.textContent = 'Long heading '.repeat(600);
    dialogBody.append(extra);
    check(dialogBody.scrollHeight > dialogBody.clientHeight, 'Long TOC cannot scroll');
    check(dialog.getBoundingClientRect().height <= win.innerHeight - 48, 'Long TOC exceeds screen');
    extra.remove();
    const originalTheme = doc.documentElement.dataset.theme;
    doc.documentElement.dataset.theme = 'dark';
    check(win.getComputedStyle(dialog).backgroundColor === 'rgb(29, 30, 32)', 'Dialog does not follow dark theme');
    doc.documentElement.dataset.theme = originalTheme;
    dialog.querySelector('a[href^="#"]').click();
    check(dialog.open && dialog.classList.contains('is-closing'), 'Heading link skipped the closing animation');
    await pause(250);
    check(!dialog.open && win.location.hash, 'Heading link did not close dialog and navigate');
    trigger.click();
    await pause(250);
    dialog.querySelector('.floating-panel-close').click();
    check(dialog.open && dialog.classList.contains('is-closing'), 'Close button skipped the closing animation');
    await pause(250);
    check(!dialog.open && doc.activeElement === trigger, 'Close did not restore focus: ' + doc.activeElement.outerHTML.slice(0, 220) + ', open=' + dialog.open);
    trigger.click();
    await pause(250);
    dialog.dispatchEvent(new win.MouseEvent('click', {clientX: 0, clientY: 0, bubbles: true}));
    check(dialog.open && dialog.classList.contains('is-closing'), 'Backdrop skipped the closing animation');
    await pause(250);
    check(!dialog.open, 'Backdrop did not close dialog');
    trigger.click();
    frame.style.width = '1600px';
    await pause();
    check(!dialog.open, 'Resize left dialog open');
    check(sidebar.querySelector('.toc'), 'Desktop TOC not restored');
    check(contentHost.parentElement === sidebar, 'Desktop layout did not restore the original content host to the sidebar');
    check(win.getComputedStyle(sidebar).position === 'fixed', 'Desktop TOC not floating');
    check(win.getComputedStyle(trigger).display === 'none', 'Desktop button visible');
    const anchorTarget = doc.getElementById('h4');
    sidebar.querySelector('a[href="#h4"]').click();
    await pause(800);
    const anchorScrollMargin = parseFloat(win.getComputedStyle(anchorTarget).scrollMarginTop);
    check(Math.abs(anchorTarget.getBoundingClientRect().top - anchorScrollMargin) <= 2, `TOC anchor ignored scroll-margin-top: headingTop=${anchorTarget.getBoundingClientRect().top}, scrollMarginTop=${anchorScrollMargin}`);
    const sideRect = sidebar.getBoundingClientRect();
    const bodyRect = doc.querySelector('.post-content').getBoundingClientRect();
    check(sideRect.left >= bodyRect.right - 1 && sideRect.right <= win.innerWidth, 'Sidebar is not to the right of the body');
    check(win.getComputedStyle(sidebar.querySelector('.floating-panel-title')).display !== 'none', 'Desktop panel title is hidden');
    const activeFrame = sidebar.querySelector('.toc-active-frame');
    const tocLinks = Array.from(sidebar.querySelectorAll('.toc a[href^="#"]'));
    const progressSegments = Array.from(sidebar.querySelectorAll('.toc-section-progress'));
    check(progressSegments.length === tocLinks.length && activeFrame, 'Missing per-section TOC progress segments or active-section frame');
    const content = doc.querySelector('.post-content');
    const headings = Array.from(content.querySelectorAll('h1, h2, h3, h4, h5, h6'));
    headings.forEach(heading => {
      const spacer = doc.createElement('div');
      spacer.style.height = '700px';
      heading.after(spacer);
    });
    win.dispatchEvent(new win.Event('resize'));
    const nextHeading = headings.find(heading => heading.id === 'h4');
    const nextHeadingTop = nextHeading.getBoundingClientRect().top + win.scrollY;
    const readingOffset = parseFloat(win.getComputedStyle(nextHeading).scrollMarginTop);
    const headerHeight = parseFloat(win.getComputedStyle(doc.documentElement).getPropertyValue('--header-height'));
    const boundaryPosition = readingOffset + (headerHeight - readingOffset) / 2;
    win.scrollTo(0, nextHeadingTop - boundaryPosition);
    win.dispatchEvent(new win.Event('scroll'));
    await pause(300);
    const boundaryActiveLinks = Array.from(sidebar.querySelectorAll('.toc a.is-active'));
    check(['#h3', '#h4'].every(hash => boundaryActiveLinks.some(link => link.hash === hash)), 'TOC reading region ignores the heading scroll-margin-top');
    win.scrollTo(0, nextHeadingTop - win.innerHeight + 140);
    win.dispatchEvent(new win.Event('scroll'));
    await pause(300);
    const activeLinks = Array.from(sidebar.querySelectorAll('.toc a.is-active'));
    const inactiveLink = sidebar.querySelector('.toc a:not(.is-active)');
    check(activeLinks.length === 2 && ['#h3', '#h4'].every(hash => activeLinks.some(link => link.hash === hash)), 'Adjacent visible sections are not highlighted together');
    check(!activeLinks.some(link => link.hash === '#h2'), 'Parent section remains highlighted while reading a child section');
    check(inactiveLink, 'Every TOC title is marked active');
    check(win.getComputedStyle(activeLinks[0]).color === resolveColor(doc, win, 'var(--primary)'), 'Active TOC title does not use the primary color');
    check(win.getComputedStyle(inactiveLink).color === resolveColor(doc, win, 'var(--secondary)'), 'Inactive TOC title does not use the configured secondary color: ' + inactiveLink.hash + ' uses ' + win.getComputedStyle(inactiveLink).color + ', expected ' + resolveColor(doc, win, 'var(--secondary)'));
    const firstSegmentRect = progressSegments[0].getBoundingClientRect();
    const firstLinkRect = sidebar.querySelector('.toc a').getBoundingClientRect();
    check(firstSegmentRect.right < firstLinkRect.left, 'TOC progress segments are not parallel to the titles');
    const previousSegment = sidebar.querySelector('.toc-section-progress[data-toc-target="h3"]');
    const currentSegment = sidebar.querySelector('.toc-section-progress[data-toc-target="h4"]');
    const inactiveSegment = sidebar.querySelector('.toc-section-progress[data-toc-target="h2"]');
    const unreadSegment = sidebar.querySelector('.toc-section-progress[data-toc-target="h5"]');
    const previousFillRect = previousSegment.querySelector('.toc-section-progress-fill').getBoundingClientRect();
    const currentFillRect = currentSegment.querySelector('.toc-section-progress-fill').getBoundingClientRect();
    check(win.getComputedStyle(currentSegment).backgroundColor === 'rgba(0, 0, 0, 0)', 'Unread progress track is not transparent');
    check(previousSegment.classList.contains('is-active') && previousFillRect.height >= previousSegment.getBoundingClientRect().height - 0.5, 'Previous visible section progress is not 100%');
    check(currentSegment.classList.contains('is-active') && currentFillRect.height > 0 && currentFillRect.height < currentSegment.getBoundingClientRect().height, 'Current section progress is not partial');
    check(parseFloat(win.getComputedStyle(inactiveSegment.querySelector('.toc-section-progress-fill')).opacity) === 0, 'Inactive section progress keeps its highlight color');
    check(inactiveSegment.classList.contains('is-read') && win.getComputedStyle(inactiveSegment).backgroundColor === resolveColor(doc, win, 'var(--tertiary)'), 'Previously read section track does not use tertiary');
    check(!unreadSegment.classList.contains('is-read') && win.getComputedStyle(unreadSegment).backgroundColor === 'rgba(0, 0, 0, 0)', 'Future unread section track is not transparent');
    const frameRect = activeFrame.getBoundingClientRect();
    const firstActiveRect = activeLinks[0].getBoundingClientRect();
    const lastActiveRect = activeLinks[activeLinks.length - 1].getBoundingClientRect();
    check(win.getComputedStyle(activeFrame).backgroundColor === resolveColor(doc, win, 'var(--code-bg)'), 'Active-section frame does not use code-bg');
    check(parseFloat(win.getComputedStyle(activeFrame).opacity) > 0.9, 'Active-section frame is hidden');
    check(frameRect.top <= firstActiveRect.top + 1 && frameRect.bottom >= lastActiveRect.bottom - 1, 'Active-section frame does not enclose all current titles');
    const top = sideRect.top;
    win.scrollTo(0, 500);
    await pause();
    check(Math.abs(sidebar.getBoundingClientRect().top - top) < 1, 'TOC scrolls offscreen');
    for (const width of [320, 390, 768, 900, 1000, 1001, 1100, 1199, 1200, 1440]) {
      frame.style.width = width + 'px';
      await pause();
      check(doc.documentElement.scrollWidth <= win.innerWidth, 'Overflow at width ' + width);
      check(doc.querySelectorAll('.toc').length === 1, 'Duplicate TOC after resize');
      if (width <= 1000) {
        const buttonRect = trigger.getBoundingClientRect();
        const progressRect = topLink.getBoundingClientRect();
        check(win.getComputedStyle(trigger).display !== 'none', 'Narrow-screen TOC button hidden at width ' + width);
        check(buttonRect.bottom < progressRect.top, 'TOC button is not above progress at width ' + width);
      } else {
        check(win.getComputedStyle(trigger).display === 'none', 'Wide-screen TOC button visible at width ' + width);
        const responsiveSideRect = sidebar.getBoundingClientRect();
        const responsiveBodyRect = doc.querySelector('.post-content').getBoundingClientRect();
        check(responsiveSideRect.left >= responsiveBodyRect.right - 1 && responsiveSideRect.right <= win.innerWidth, 'Sidebar overlaps the responsive body at width ' + width);
      }
    }
    async function checkPostNav(path, direction) {
      await load(path);
      const navDoc = frame.contentDocument, navWin = frame.contentWindow;
      const link = navDoc.querySelector(`.paginav .${direction}`);
      const arrow = link?.querySelector('.paginav-arrow');
      const label = link?.querySelector('.paginav-label');
      check(link && arrow && label && arrow.matches('svg[aria-hidden="true"]'), `Missing ${direction} navigation arrow structure`);
      check(parseFloat(navWin.getComputedStyle(arrow).opacity) === 0, `${direction} navigation arrow is visible before interaction`);
      link.focus();
      await pause(250);
      const labelShift = new navWin.DOMMatrix(navWin.getComputedStyle(label).transform).m41;
      check(parseFloat(navWin.getComputedStyle(arrow).opacity) > 0.9, `${direction} navigation arrow does not appear on focus`);
      check(direction === 'prev' ? labelShift > 0 : labelShift < 0, `${direction} article title does not move inward for the arrow`);
    }
    await checkPostNav('/posts/20260805hello-world/', 'prev');
    await checkPostNav('/posts/20260928some-notes/', 'next');
    await load('/posts/');
    const listDoc = frame.contentDocument, listWin = frame.contentWindow;
    const tagsPanel = listDoc.querySelector('.floating-panel[data-panel-id="tags"]');
    check(tagsPanel, 'Posts tags are not rendered through the shared floating panel');
    const tagsSidebar = tagsPanel.querySelector('#tags-sidebar');
    const tagsTrigger = tagsPanel.querySelector('#tags-trigger');
    const tagsDialog = tagsPanel.querySelector('#tags-dialog');
    const tagsHost = tagsPanel.querySelector('.floating-panel-content');
    const tagNav = tagsPanel.querySelector('.category-nav');
    const tagButtons = Array.from(tagsPanel.querySelectorAll('.category-btn'));
    const helloEntry = Array.from(listDoc.querySelectorAll('.post-entry')).find(entry => entry.querySelector('.entry-link')?.pathname === '/posts/20260805hello-world/');
    const listCover = helloEntry?.querySelector('.entry-cover-list');
    const listCoverImage = listCover?.querySelector('img');
    check(tagsSidebar && tagsTrigger && tagsDialog && tagsHost && tagNav, 'Tags panel structure is incomplete');
    check(helloEntry && listCover && listCoverImage, 'Post entry cover structure is incomplete');
    const listCoverStyle = listWin.getComputedStyle(listCover);
    const helloEntryRect = helloEntry.getBoundingClientRect();
    const listCoverRect = listCover.getBoundingClientRect();
    check(listCoverStyle.position === 'absolute' && Math.abs(listCoverRect.right - helloEntryRect.right) <= 1, `Post entry cover is not fixed to the right side: position=${listCoverStyle.position}, coverRight=${listCoverRect.right}, entryRight=${helloEntryRect.right}`);
    check(parseFloat(listCoverStyle.opacity) < 1 && (listCoverStyle.maskImage !== 'none' || listCoverStyle.webkitMaskImage !== 'none'), 'Post entry cover does not fade toward the left');
    check(listWin.getComputedStyle(listCoverImage).objectFit === 'cover' && !listCover.querySelector('a'), 'Post entry cover is not a non-clickable background image');
    const helloEntryLink = helloEntry.querySelector('.entry-link');
    check(helloEntryLink?.pathname === '/posts/20260805hello-world/', 'Post entry no longer links to the article');
    const helloTitleRect = helloEntry.querySelector('.entry-header').getBoundingClientRect();
    const helloTitleHit = listDoc.elementFromPoint(helloTitleRect.left + 8, helloTitleRect.top + helloTitleRect.height / 2);
    check(helloTitleHit?.closest('.entry-link') === helloEntryLink, `Post entry title area is not clickable: hit=${helloTitleHit?.className || helloTitleHit?.tagName}`);
    check(!listDoc.querySelector('.main > .category-nav'), 'Old inline tags navigation remains in the left column');
    check(tagButtons.length >= 3 && tagButtons.every(link => link.pathname.startsWith('/tags/') && link.querySelector('sup')?.textContent.trim()), 'Tag links or counts changed');
    check(listWin.getComputedStyle(tagNav).flexWrap === 'wrap', 'Tags do not wrap');
    check(parseFloat(listWin.getComputedStyle(tagButtons[0]).borderRadius) > 0, 'Tag buttons lost their rounded style');
    check(listWin.getComputedStyle(tagsSidebar).position === 'fixed', 'Desktop tags sidebar is not fixed');
    const tagsSideRect = tagsSidebar.getBoundingClientRect();
    const firstEntryRect = listDoc.querySelector('.post-entry').getBoundingClientRect();
    check(tagsSideRect.left >= firstEntryRect.right - 1 && tagsSideRect.right <= listWin.innerWidth, 'Tags sidebar overlaps post entries');
    check(listWin.getComputedStyle(tagsTrigger).display === 'none', 'Desktop tags trigger is visible');
    for (const width of [320, 390, 768, 900, 1000]) {
      frame.style.width = width + 'px';
      await pause();
      check(listDoc.documentElement.scrollWidth <= listWin.innerWidth, 'Posts overflow at width ' + width);
      check(listWin.getComputedStyle(tagsTrigger).display !== 'none' && !tagsTrigger.hidden, 'Tags trigger hidden at width ' + width);
      check(listWin.getComputedStyle(tagsSidebar).display === 'none', 'Tags sidebar visible at width ' + width);
      check(Math.abs(listWin.innerHeight - tagsTrigger.getBoundingClientRect().bottom - 110) < 1, 'Tags trigger is too high at width ' + width);
    }
    tagsTrigger.click();
    check(tagsDialog.open && tagsHost.parentElement === tagsDialog.querySelector('.floating-panel-dialog-body'), 'Tags dialog did not open with the original content host');
    check(listWin.getComputedStyle(tagsDialog).animationName === 'floating-panel-dialog-in', 'Tags dialog does not use the shared animation');
    await pause(250);
    const tagsDialogRect = tagsDialog.getBoundingClientRect();
    check(Math.abs(tagsDialogRect.left + tagsDialogRect.width / 2 - listWin.innerWidth / 2) < 2, 'Tags dialog is not horizontally centered');
    check(Math.abs(tagsDialogRect.top + tagsDialogRect.height / 2 - listWin.innerHeight / 2) < 2, 'Tags dialog is not vertically centered');
    const extraTags = listDoc.createElement('div');
    extraTags.textContent = 'tag '.repeat(1500);
    tagsHost.append(extraTags);
    const tagsDialogBody = tagsDialog.querySelector('.floating-panel-dialog-body');
    check(tagsDialogBody.scrollHeight > tagsDialogBody.clientHeight, 'Long tags dialog cannot scroll');
    extraTags.remove();
    tagsDialog.querySelector('.floating-panel-close').click();
    await pause(250);
    check(!tagsDialog.open && listDoc.activeElement === tagsTrigger, 'Tags dialog close did not restore focus');
    frame.style.width = '1440px';
    await pause(300);
    check(tagsHost.parentElement === tagsSidebar && listWin.getComputedStyle(tagsSidebar).position === 'fixed', 'Tags content was not restored to the desktop sidebar: media=' + listWin.matchMedia('(min-width: 1001px)').matches + ', parent=' + tagsHost.parentElement?.className);
    check(listDoc.getElementById('top-link').classList.contains('hidden'), 'List-page top link behavior changed');
    await load('/tags/test/');
    check(!frame.contentDocument.querySelector('.floating-panel[data-panel-id="tags"]'), 'Tags panel rendered on a list page without showTags');
    const fixtures = document.createElement('div');
    fixtures.innerHTML = `
      <div class="floating-panel" data-panel-id="incomplete"><button class="floating-panel-trigger" hidden></button></div>
      <div class="floating-panel" data-panel-id="one">
        <button class="floating-panel-trigger" hidden></button><aside class="floating-panel-sidebar"><div class="floating-panel-content"><svg aria-label="element content"></svg></div></aside>
        <dialog class="floating-panel-dialog"><button class="floating-panel-close"></button><div class="floating-panel-dialog-body"></div></dialog>
      </div>
      <div class="floating-panel" data-panel-id="two">
        <button class="floating-panel-trigger" hidden></button><aside class="floating-panel-sidebar"><div class="floating-panel-content">second panel</div></aside>
        <dialog class="floating-panel-dialog"><button class="floating-panel-close"></button><div class="floating-panel-dialog-body"></div></dialog>
      </div>`;
    document.body.append(fixtures);
    await loadScript('/floating-panel-test.js');
    const firstFixture = fixtures.querySelector('[data-panel-id="one"]');
    const secondFixture = fixtures.querySelector('[data-panel-id="two"]');
    const firstFixtureTrigger = firstFixture.querySelector('.floating-panel-trigger');
    const secondFixtureTrigger = secondFixture.querySelector('.floating-panel-trigger');
    check(!firstFixtureTrigger.hidden && !secondFixtureTrigger.hidden, 'Valid element-only or later panel did not initialize after an incomplete panel');
    firstFixtureTrigger.click();
    secondFixtureTrigger.click();
    check(firstFixture.querySelector('dialog').open && secondFixture.querySelector('dialog').open && document.documentElement.classList.contains('floating-panel-modal-open'), 'Multiple panels did not open independently');
    firstFixture.querySelector('.floating-panel-close').click();
    await pause(300);
    check(secondFixture.querySelector('dialog').open && document.documentElement.classList.contains('floating-panel-modal-open'), 'Closing one panel unlocked the page while another panel remained open');
    secondFixture.querySelector('.floating-panel-close').click();
    await pause(300);
    check(!document.documentElement.classList.contains('floating-panel-modal-open'), 'Closing the last panel left the page locked');
    document.body.setAttribute('data-result', 'PASS');
  } catch (error) {
    document.body.setAttribute('data-result', 'FAIL: ' + error.message);
  } finally {
    await fetch('/done');
  }
})();
</script></body></html>'''

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    finished = threading.Event()

    def do_GET(self):
        # Keep the document loading until real browser events finish the checks.
        if self.path in ('/hold', '/done'):
            if self.path == '/hold':
                self.finished.wait(20)
            else:
                self.finished.set()
            self.send_response(200)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, *_):
        pass

with tempfile.TemporaryDirectory(prefix="hugo-toc-test-") as directory:
    build = Path(directory) / "site"
    fixture_content = Path(directory) / "content"
    shutil.copytree(ROOT / "content", fixture_content)
    fixture_post = fixture_content / "posts/20260805hello-world/index.md"
    fixture_text = fixture_post.read_text(encoding="utf-8")
    if re.search(r"(?m)^source\s*=", fixture_text):
        fixture_text = re.sub(r"(?m)^source\s*=.*$", "source = 'https://images.example.test/manhattan'", fixture_text, count=1)
    elif "[cover]" in fixture_text:
        fixture_text = fixture_text.replace("[cover]", "[cover]\nsource = 'https://images.example.test/manhattan'", 1)
    else:
        frontmatter_end = fixture_text.find("+++", 3)
        fixture_text = fixture_text[:frontmatter_end] + "[cover]\nimage = '曼哈顿-宇宙无敌汪师傅.png'\nalt = '曼哈顿城市景观'\nsource = 'https://images.example.test/manhattan'\n" + fixture_text[frontmatter_end:]
    fixture_post.write_text(fixture_text, encoding="utf-8")
    subprocess.run(["hugo", "--contentDir", str(fixture_content), "--destination", str(build), "--noBuildLock"], cwd=ROOT, check=True)
    (build / "toc-test.html").write_text(CHECKS, encoding="utf-8")
    shutil.copyfile(THEME / "assets/js/floating-panel.js", build / "floating-panel-test.js")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(build)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        result = subprocess.run([
            str(BROWSER), "--headless", "--disable-gpu", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions",
            "--user-data-dir=" + str(Path(directory) / "profile"),
            "--disable-background-timer-throttling", "--dump-dom",
            f"http://127.0.0.1:{server.server_port}/toc-test.html",
        ], capture_output=True, text=True, encoding="utf-8", timeout=45)
        status = re.search(r'data-result="([^"]*)"', result.stdout)
        print(status.group(1) if status else result.stderr[-2000:])
        if not status or status.group(1) != "PASS":
            raise SystemExit(1)
    finally:
        server.shutdown()
