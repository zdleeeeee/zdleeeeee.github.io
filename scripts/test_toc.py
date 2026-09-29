"""Build into a temporary directory and check the TOC in headless Chrome."""
import functools
import http.server
import os
from pathlib import Path
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
BROWSER = Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"

CHECKS = r'''<!doctype html><html><body><img src="/hold" hidden><iframe id="page" style="width:390px;height:844px;border:0"></iframe>
<script>
const frame = document.getElementById('page');
const pause = (milliseconds = 150) => new Promise(resolve => setTimeout(resolve, milliseconds));
function check(value, message) { if (!value) throw new Error(message); }
function load(path) { return new Promise(resolve => { frame.onload = resolve; frame.src = path; }); }
function resolveColor(doc, win, value) {
  const sample = doc.createElement('span');
  sample.style.color = value;
  doc.body.append(sample);
  const color = win.getComputedStyle(sample).color;
  sample.remove();
  return color;
}
(async () => {
  try {
    await load('/posts/20260805hello-world/');
    const doc = frame.contentDocument, win = frame.contentWindow;
    const trigger = doc.getElementById('toc-trigger');
    const dialog = doc.getElementById('toc-dialog');
    const topLink = doc.getElementById('top-link');
    const progress = topLink?.querySelector('.reading-progress');
    const progressArrow = topLink?.querySelector('.progress-arrow');
    check(trigger && dialog, 'Missing TOC button/dialog');
    check(topLink && progress, 'Missing reading progress control');
    check(progressArrow, 'Missing rounded progress arrow');
    check(win.getComputedStyle(topLink).visibility === 'visible', 'Post progress control is not always visible');
    check(progress.textContent === '0%', 'Reading progress does not start at 0%');
    check(win.getComputedStyle(progress).opacity === '1' && win.getComputedStyle(progressArrow).opacity === '0', 'Progress and arrow initial visibility is wrong');
    check(win.getComputedStyle(progress).transitionDuration === '0.2s', 'Progress fade duration is not 200ms');
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
    check(openingStyle.animationName === 'toc-dialog-in' && openingStyle.animationDuration === '0.2s', 'Dialog does not use the 200ms opening animation');
    check(dialog.contains(doc.activeElement), 'Focus did not enter dialog');
    check(!dialog.querySelector('details, summary'), 'TOC remains collapsible');
    const tocTitle = dialog.querySelector('.toc-title');
    check(tocTitle && win.getComputedStyle(tocTitle).display === 'none', 'Dialog repeats the desktop TOC title');
    await pause(250);
    const rect = dialog.getBoundingClientRect();
    check(Math.abs(rect.left + rect.width / 2 - win.innerWidth / 2) < 2, 'Dialog not horizontally centered');
    check(Math.abs(rect.top + rect.height / 2 - win.innerHeight / 2) < 2, 'Dialog not vertically centered');
    const dialogBody = dialog.querySelector('.toc-dialog-body');
    const tocInner = dialog.querySelector('.toc .inner');
    const tocLink = tocInner.querySelector('a[href^="#"]');
    const innerStyle = win.getComputedStyle(tocInner);
    check(Array.from(tocInner.querySelectorAll('ul')).every(list => win.getComputedStyle(list).listStyleType === 'none'), 'TOC list markers remain visible');
    check(parseFloat(innerStyle.paddingLeft) >= 12 && parseFloat(innerStyle.paddingRight) >= 12, 'TOC content padding is missing');
    check(win.getComputedStyle(tocLink).display === 'block', 'TOC heading is not a full-row link');
    const linkRect = tocLink.getBoundingClientRect();
    const rowEdgeTarget = doc.elementFromPoint(linkRect.right - 2, linkRect.top + linkRect.height / 2);
    check(rowEdgeTarget?.closest('a') === tocLink, 'TOC row edge is not clickable');
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
    dialog.querySelector('.toc-close').click();
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
    const sidebar = doc.getElementById('toc-sidebar');
    check(sidebar.querySelector('.toc'), 'Desktop TOC not restored');
    check(win.getComputedStyle(sidebar).position === 'fixed', 'Desktop TOC not floating');
    check(win.getComputedStyle(trigger).display === 'none', 'Desktop button visible');
    const sideRect = sidebar.getBoundingClientRect();
    const bodyRect = doc.querySelector('.post-content').getBoundingClientRect();
    check(sideRect.left >= bodyRect.right - 1 && sideRect.right <= win.innerWidth, 'Sidebar is not to the right of the body');
    check(win.getComputedStyle(sidebar.querySelector('.toc-title')).display !== 'none', 'Desktop TOC title is hidden');
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
    await load('/posts/');
    check(!frame.contentDocument.getElementById('toc-trigger') || frame.contentDocument.getElementById('toc-trigger').hidden, 'TOC button on list page');
    check(frame.contentDocument.getElementById('top-link').classList.contains('hidden'), 'List-page top link behavior changed');
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
    subprocess.run(["hugo", "--destination", str(build), "--noBuildLock"], cwd=ROOT, check=True)
    (build / "toc-test.html").write_text(CHECKS, encoding="utf-8")
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
        import re
        status = re.search(r'data-result="([^"]*)"', result.stdout)
        print(status.group(1) if status else result.stderr[-2000:])
        if not status or status.group(1) != "PASS":
            raise SystemExit(1)
    finally:
        server.shutdown()
