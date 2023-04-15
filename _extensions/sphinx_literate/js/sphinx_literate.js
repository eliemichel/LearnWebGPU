// NB: This style has been designed for the Furo theme.

// Read-only
const config = {
	//begin_ref: "{{\u00a0",
	//end_ref: "\u00a0}}",
	begin_ref: "{{",
	end_ref: "}}",
};

// Options tunable by the user
class Options {
	constructor() {
		this.changedEvent = new Event("litOptionsChanged");

		this.defaultOptions = {
			showBlockName: false,
			showReferenceDetails: false,
			showReferenceLinks: false,
			showHiddenLinks: false,
			showHiddenBlocks: false,
		}

		for (const [key, value] of Object.entries(this.defaultOptions)) {
			if (localStorage.getItem(key) === null) {
				console.log("Initializing option " + key);
				localStorage.setItem(key, JSON.stringify(value));
			} else {
				console.log("Loaded option " + key + ": " + JSON.parse(localStorage.getItem(key)));
			}
		}
	}

	get(key) {
		return JSON.parse(localStorage.getItem(key));
	}

	set(key, value) {
		localStorage.setItem(key, JSON.stringify(value));
		document.dispatchEvent(this.changedEvent);
	}
}
const options = new Options();

const lightStyleVariables = `
--color-background-lit-info: #d5eca8;
--color-foreground-lit-info: rgb(113, 138, 26);
--color-foreground-hover-lit-comment-ref: #353328;
`;

const darkStyleVariables = `
--color-background-lit-info: #3e3d35;
//--color-foreground-lit-info: rgba(0, 0, 0, 0.39);
--color-foreground-lit-info: rgb(142, 142, 142);
--color-foreground-hover-lit-comment-ref: #97906f;
`;

// Reproduce Furo's light/dark theme mechanism
const styleVariables = `
body {
	${lightStyleVariables}
}

@media not print {
body[data-theme="dark"] {
	${darkStyleVariables}
}

@media (prefers-color-scheme: dark) {
body:not([data-theme="light"]) {
	${darkStyleVariables}
}
}
}

/* Global style as well */
.content-icon-container .literate-options button {
	border: none;
	background: none;
	margin: 0;
	padding: 0;
	cursor: pointer;
}
.content-icon-container .literate-options svg {
  color: inherit;
  height: 1rem;
  width: 1rem;
}

.lit-block-hidden {
	display: none;
}
body[data-lit-block-show-hidden="true"] .lit-block-hidden {
	display: block;	
}
`;

const commonStyle = `
a:hover {
	color: var(--color-link--hover);
	-webkit-text-decoration-color: var(--color-link-underline--hover);
	text-decoration-color: var(--color-link-underline--hover);
}
a {
	color: var(--color-link);
	text-decoration: underline;
	text-decoration-color: currentcolor;
	-webkit-text-decoration-color: var(--color-link-underline);
	text-decoration-color: var(--color-link-underline);
}
a {
	background-color: transparent;
}
`;

const litRefStyle = `
.comment {
	/* from pygment */
	color: #75715e;
	font-style: italic;
}
a.comment:hover {
	color: var(--color-foreground-hover-lit-comment-ref);
}
`;

const litBlockInfoStyle = `
.wrapper {
	text-align: right;
	font-size: 0.8em;
	position: absolute;
	bottom: -0.7em;
	right: 0.5em;
	margin-top: 0;
	color: var(--color-foreground-lit-info);
	background-color: var(--color-background-lit-info);
	border-radius: 0.3em;
	padding: 0 0.3em;
}

.wrapper a.lit-name {
	color: rgba(0, 0, 0, 0.94);
}
`;

function buildComment(content, lexer) {
	// TODO: get comment format from Sphinx lexer automatically?
	lexer = lexer.toLowerCase();
	if (["python", "cmake"].includes(lexer)) {
		return "# " + content;
	}
	else if (["c++", "c", "javascript", "js"].includes(lexer)) {
		return "// " + content;
	}
	else if (["css"].includes(lexer)) {
		return "/* " + content + " */";
	}
	else {
		return content;
	}
}

/**
 * Wrap the line that contains the element in a span with the given class name.
 */
function createLineWrapper(element, className) {
	const parentPre = element.closest("pre");

	let parent = element.parentNode;
	let container = element;
	while (parent != parentPre) {
		container = parent;
		parent = parent.parentNode;
	}

	const containerIndex = [].indexOf.call(parentPre.childNodes, container);

	const elementsOnSameLine = [container];
	// Find all next nodes on the same line
	for (let i = containerIndex + 1 ; i < parentPre.childNodes.length ; ++i) {
		const node = parentPre.childNodes[i];
		const nlIdx = node.nodeValue === null ? -1 : node.nodeValue.indexOf("\n");
		if (node.nodeType === Node.TEXT_NODE && nlIdx != -1) {
			if (nlIdx === node.nodeValue.length - 1) {
				elementsOnSameLine.push(node);
			} else {
				// Split text node after the first new line
				const nodeSecondHalf = document.createTextNode(node.nodeValue.substring(nlIdx + 1));
				node.nodeValue = node.nodeValue.substring(0, nlIdx + 1);
				elementsOnSameLine.push(node);
				parentPre.insertBefore(nodeSecondHalf, node.nextSibling);
			}
			break;
		}
		elementsOnSameLine.push(node);
	}
	// Find all previous nodes on the same line
	for (let i = containerIndex - 1 ; i >= 0 ; --i) {
		const node = parentPre.childNodes[i];
		if (node.nodeType === Node.TEXT_NODE && node.nodeValue.indexOf("\n") != -1) {
			break;
		}
		elementsOnSameLine.unshift(node);
	}

	lineWrapper = document.createElement('span');
	lineWrapper.setAttribute("class", className);
	parentPre.insertBefore(lineWrapper, elementsOnSameLine[0]);
	lineWrapper.append(...elementsOnSameLine);
	return lineWrapper;
}

class LitRef extends HTMLElement {
	constructor() {
		super();

		const shadow = this.attachShadow({ mode: "open" });

		this.styleElement = document.createElement("style");
		this.styleElement.textContent = commonStyle + litRefStyle;

		this.rebuildShadow();

		// Callbacks
		document.addEventListener(options.changedEvent.type, (function() {
			this.rebuildShadow();
		}).bind(this));
	}

	rebuildShadow() {
		const hidden = this.getAttribute("hidden-link") === "true" && !options.get('showHiddenLinks');
		if (hidden) {
			let lineWrapper = this.closest(".lit-line-wrapper");
			if (lineWrapper === null) {
				lineWrapper = createLineWrapper(this, "lit-line-wrapper");
			}
			lineWrapper.setAttribute("style", "display: none;");
		} else {
			let lineWrapper = this.closest(".lit-line-wrapper");
			if (lineWrapper !== null) {
				lineWrapper.setAttribute("style", "");
			}
		}

		if (options.get('showReferenceLinks')) {
			const open = document.createTextNode(config.begin_ref);

			const close = document.createTextNode(config.end_ref);

			const link = document.createElement("a");
			link.textContent = this.getAttribute("name");
			link.href = this.getAttribute("href");

			this.shadowRoot.replaceChildren(this.styleElement, open, link, close);
		} else {
			const comment = document.createElement("a");
			comment.setAttribute("class", "comment");
			comment.setAttribute("href", this.getAttribute("href"));
			let lexer = null;
			if (this.hasAttribute("lexer")) {
				lexer = this.getAttribute("lexer");
			}
			comment.textContent = buildComment("[...] " + this.getAttribute("name"), lexer);

			this.shadowRoot.replaceChildren(this.styleElement, comment);
		}
	}
}

customElements.define("lit-ref", LitRef);

class LitBlockInfo extends HTMLElement {
	constructor() {
		super();

		this.attachShadow({ mode: "open" });

		this.styleElement = document.createElement("style");
		this.styleElement.textContent = commonStyle + litBlockInfoStyle;

		this.rebuildShadow();

		// Callbacks
		document.addEventListener(options.changedEvent.type, (function() {
			this.rebuildShadow();
		}).bind(this));
	}

	rebuildShadow() {
		const data = JSON.parse(this.getAttribute("data"));

		const wrapper = document.createElement("div");
		wrapper.setAttribute("class", "wrapper");
		wrapper.setAttribute("data-theme", "dark");

		if (options.get('showBlockName')) {
			wrapper.append(...this.createLitLink(data.name, data.permalink, "lit-name"));
		}

		if (options.get('showReferenceDetails')) {
			const details = [
				'replaced by',
				'completed in',
				'completing',
				'prepended in',
				'prepending',
				'patched by',
				'replacing',
				'referenced in',
				'inserted in'
			];
			details.map(section => {
				if (data[section].length > 0) {
					wrapper.append(document.createTextNode(" " + section + " "));
					data[section].map(lit => {
						wrapper.append(...this.createLitLink(lit.name, lit.url));
						if (lit.details) {
							wrapper.append(document.createTextNode(" " + lit.details));
						}
					});
				}
			});
		}

		this.shadowRoot.replaceChildren(this.styleElement, wrapper);
	}

	createLitLink(name, url, className) {
		const open = document.createTextNode(config.begin_ref);

		const close = document.createTextNode(config.end_ref);

		const link = document.createElement("a");
		link.textContent = name;
		link.href = url;
		if (className !== undefined) {
			link.setAttribute("class", className);
		}

		return [open, link, close];
	}
}

customElements.define("lit-block-info", LitBlockInfo);

const literateBtnTemplate = `
<button title="Literate options">
	<svg aria-hidden="true" viewBox="0 0 67.733333 67.733334" stroke-width="3.54809" stroke="currentColor" fill="currentColor" stroke-linecap="butt" stroke-linejoin="round">
		<path style="fill:none" d="M 22.022455,7.2758939 C 20.236913,30.293765 60.886421,32.147289 59.767779,15.820185 59.329234,9.4257407 48.281466,3.3350703 42.527879,22.635036 37.299835,40.172082 24.145493,43.709247 13.533714,42.757932 0.13866865,41.557256 0.20324393,27.149302 6.9501566,25.08928 13.820684,22.991562 20.372308,29.520422 25.149318,44.361387 c 6.394941,19.86776 18.523459,24.743831 27.165621,16.604648 6.719662,-6.32852 6.253443,-15.45748 -0.127732,-21.097386" />
		<circle style="stroke:none" cx="55.142498" cy="14.859671" r="4.1102643" />
		<path style="fill:none" d="M 66.876312,8.2790248 H 62.461917 C 58.988759,4.1122728 50.780458,1.4458099 44.559942,7.6510133 H 40.24461" />
	</svg>
	<span class="visually-hidden">Literate options</span>
</button>
`;

// Inject in Furo theme
function onDOMContentLoaded() {
	// Add global style
	const style = document.createElement("style");
	style.textContent = styleVariables;
	document.head.append(style);

	// Add literate button (could be done through the template, anyway, not used ATM)
	/*
	const containers = document.querySelectorAll(".content-icon-container")
	for (let i = 0 ; i < containers.length ; ++i) {
		const literateBtn = document.createElement("div");
		literateBtn.setAttribute("class", "literate-options");
		literateBtn.innerHTML = literateBtnTemplate;
		containers[i].insertBefore(literateBtn, containers[i].children[0]);
	}
	*/

	// Connect elements to literate options
	const checkboxIdToOption = {
		"lit-opts-show-block-name": "showBlockName",
		"lit-opts-show-reference-details": "showReferenceDetails",
		"lit-opts-show-reference-links": "showReferenceLinks",
		"lit-opts-show-hidden-links": "showHiddenLinks",
		"lit-opts-show-hidden-blocks": "showHiddenBlocks",
	}
	for (const [id, opt] of Object.entries(checkboxIdToOption)) {
		const input = document.getElementById(id);
		if (input === null) continue;
		input.checked = options.get(opt);
		input.addEventListener('click', function(e) {
			options.set(opt, input.checked);
		});
	}

	document.body.setAttribute("data-lit-block-show-hidden", options.get("showHiddenBlocks"));
	document.addEventListener(options.changedEvent.type, function() {
		document.body.setAttribute("data-lit-block-show-hidden", options.get("showHiddenBlocks"));
	});
}
document.addEventListener('DOMContentLoaded', onDOMContentLoaded, {once: true});