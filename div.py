from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import re
import hashlib
import secrets
import os
import smtplib
from email.message import EmailMessage
from urllib.parse import urlparse


ROOT = Path(__file__).parent
ACCOUNT_FILE = ROOT / "accounts.json"

CHALLENGES = [
	{
		"id": 1,
		"title": "Make cooling centers easier to reach",
		"summary": "How might we help older adults find and safely reach public cooling spaces during extreme heat?",
		"category": "Climate resilience",
		"stage": "Open for ideas",
		"organization": "City of Phoenix",
		"organization_type": "Civic partner",
		"location": "Phoenix, AZ",
		"time": "2 days ago",
		"participants": 28,
		"ideas": 14,
		"impact": "18k residents",
		"tags": ["public health", "heat", "accessibility"],
		"featured": True,
	},
	{
		"id": 2,
		"title": "Rethink food waste on campus",
		"summary": "Design a practical campus system that turns surplus dining hall food into reliable community meals.",
		"category": "Food systems",
		"stage": "Seeking partners",
		"organization": "University of Michigan",
		"organization_type": "University",
		"location": "Ann Arbor, MI",
		"time": "1 week ago",
		"participants": 41,
		"ideas": 22,
		"impact": "2.4 tons / week",
		"tags": ["circular economy", "community", "logistics"],
		"featured": False,
	},
	{
		"id": 3,
		"title": "A safer night bus for every rider",
		"summary": "Explore low-cost service and design changes that make late-night transit feel safer and more predictable.",
		"category": "Mobility",
		"stage": "In research",
		"organization": "Lumen Transit Lab",
		"organization_type": "Industry partner",
		"location": "Toronto, ON",
		"time": "5 days ago",
		"participants": 19,
		"ideas": 9,
		"impact": "12 routes",
		"tags": ["transit", "safety", "service design"],
		"featured": False,
	},
	{
		"id": 4,
		"title": "Create safer crossings near schools",
		"summary": "Help communities identify and improve the street crossings where children and families feel least safe every day.",
		"category": "Public safety",
		"stage": "Open for ideas",
		"organization": "Ranchi Municipal Corporation",
		"organization_type": "Local body",
		"location": "Ranchi, Jharkhand",
		"time": "4 days ago",
		"participants": 12,
		"ideas": 6,
		"impact": "Safer school journeys",
		"tags": ["mobility", "children", "community safety"],
		"featured": False,
	},
	{
		"id": 5,
		"title": "Build a societal innovation collaboration platform",
		"summary": "Connect citizens who identify local challenges with universities, industry partners, startups, and government teams ready to create measurable solutions together.",
		"category": "Societal innovation",
		"stage": "Open for collaboration",
		"organization": "Common Ground community",
		"organization_type": "Community network",
		"location": "India",
		"time": "1 week ago",
		"participants": 34,
		"ideas": 18,
		"impact": "Stronger communities",
		"tags": ["citizen engagement", "universities", "industry", "public impact"],
		"featured": True,
		"background": "Communities identify local challenges across education, healthcare, agriculture, water, sanitation, environment, livelihoods, accessibility, infrastructure, and public services. Citizens often see these issues first, while universities hold research capacity and industry holds technical, financial, and implementation capability. This platform brings those strengths together in one transparent innovation ecosystem.",
		"requirements": [
			"Collect challenges from citizens, community groups, local bodies, and government with photos, videos, location, and documents.",
			"Categorize, prioritize, deduplicate, and route validated problems using AI-assisted analysis.",
			"Match challenges to universities using disciplines, faculty expertise, research facilities, and incubation capacity.",
			"Help universities form multidisciplinary student and faculty teams and submit solution proposals.",
			"Connect industry, startups, MSMEs, CSR organizations, labs, and innovation hubs for mentorship, funding, prototyping, testing, and deployment.",
			"Track review, assignment, communication, milestones, deliverables, approvals, testing, IP, and implementation status.",
			"Give departments dashboards for submissions, domains, institutions, industry engagement, progress, innovation outcomes, and community impact.",
		],
		"expected_solution": [
			"Citizen engagement module with multimedia evidence and geographic context.",
			"AI-enabled problem management and institutional routing.",
			"University collaboration, team formation, mentoring, and proposal management.",
			"Industry partnership for co-development, funding, pilots, and technology transfer.",
			"Project lifecycle management with milestones and validation.",
			"Visual analytics plus notifications and communication across the project lifecycle.",
		],
	},
	{
		"id": 6,
		"title": "AI early warning for landslide risk",
		"summary": "Combine rainfall, terrain, satellite, and ground data to monitor landslide risk and help communities and authorities act before disaster strikes.",
		"category": "Disaster management",
		"stage": "Open for research teams",
		"organization": "Regional resilience network",
		"organization_type": "Public safety partner",
		"location": "Northeast India",
		"time": "1 week ago",
		"participants": 16,
		"ideas": 8,
		"impact": "Safer hillside communities",
		"tags": ["landslides", "early warning", "geospatial AI", "community safety"],
		"featured": True,
	},
	{
		"id": 7,
		"title": "Intelligent urban land records",
		"summary": "Bring maps, cadastral records, satellite imagery, and civic datasets together for accurate, searchable, and transparent urban land management.",
		"category": "Geospatial governance",
		"stage": "Open for data partners",
		"organization": "Urban planning network",
		"organization_type": "Civic innovation partner",
		"location": "Urban India",
		"time": "5 days ago",
		"participants": 21,
		"ideas": 11,
		"impact": "Smarter land services",
		"tags": ["GIS", "land records", "satellite data", "urban planning"],
		"featured": True,
	},
	{
		"id": 8,
		"title": "Geospatial intelligence for watershed development",
		"summary": "Use geo-coded images and spatial analysis to help watershed teams plan, monitor, and improve water and land development outcomes.",
		"category": "Watershed development",
		"stage": "Open for geospatial ideas",
		"organization": "Watershed development network",
		"organization_type": "Rural development partner",
		"location": "Rural India",
		"time": "4 days ago",
		"participants": 14,
		"ideas": 7,
		"impact": "Healthier watersheds",
		"tags": ["geospatial", "geo-coded images", "water resources", "monitoring"],
		"featured": True,
	},
	{
		"id": 9,
		"title": "Cooperative gig services for every community",
		"summary": "Build a cooperative-owned marketplace that connects verified electricians, plumbers, caregivers, drivers, cleaners, and other skilled workers with households and institutions.",
		"category": "Cooperative services",
		"stage": "Open for product teams",
		"organization": "Labour cooperative network",
		"organization_type": "Cooperative partner",
		"location": "India",
		"time": "3 days ago",
		"participants": 27,
		"ideas": 13,
		"impact": "Fair work for communities",
		"tags": ["cooperatives", "skilled workers", "digital payments", "AI forecasting"],
		"featured": True,
		"background": "Labour cooperatives have skilled workers and strong local presence, but lack a structured digital platform to connect them with households and institutions. A cooperative-owned service marketplace can improve worker utilization while ensuring fair wages, welfare, and consumer trust.",
		"requirements": [
			"Register and verify service providers with skill profiles and certifications.",
			"Let customers discover, book, and schedule household and community services.",
			"Match customers and workers using geolocation, availability, skills, and service area.",
			"Support digital payments, invoices, ratings, and feedback.",
			"Integrate worker welfare, insurance, emergency, and on-demand services.",
			"Provide a multilingual mobile experience for workers and customers.",
			"Use AI for demand forecasting and workforce allocation.",
			"Give cooperative federations an administration dashboard for operations and impact.",
		],
		"expected_solution": [
			"Verified provider onboarding and certification management.",
			"Customer booking, scheduling, service tracking, and notifications.",
			"Geospatial service matching and real-time worker availability.",
			"Digital payments, invoicing, ratings, and dispute support.",
			"Worker welfare, insurance, emergency booking, and fair-work records.",
			"AI demand prediction, workforce allocation, and cooperative analytics.",
		],
 	},
]

try:
	ACCOUNTS = json.loads(ACCOUNT_FILE.read_text(encoding="utf-8")) if ACCOUNT_FILE.exists() else {}
except (OSError, json.JSONDecodeError):
	ACCOUNTS = {}

DEMO_EMAIL = os.environ.get("COMMON_GROUND_DEMO_EMAIL", "demo@aerosols.com")
DEMO_PASSWORD = os.environ.get("COMMON_GROUND_DEMO_PASSWORD", "Aerosols123!")


def ensure_demo_account():
	account = ACCOUNTS.get(DEMO_EMAIL)
	if account is None:
		ACCOUNTS[DEMO_EMAIL] = {"password": password_hash(DEMO_PASSWORD), "photo": ""}
		save_accounts()
	elif account.get("password") != password_hash(DEMO_PASSWORD):
		account["password"] = password_hash(DEMO_PASSWORD)
		account["photo"] = account.get("photo", "")
		save_accounts()
	return DEMO_EMAIL, DEMO_PASSWORD


RESET_CODES = {}
ACTIVITY = {}
CERTIFICATES = {}
UNIVERSITY_ROUTES = {
	"education": "Central University of Jharkhand",
	"healthcare": "Rajendra Institute of Medical Sciences",
	"agriculture": "Birsa Agricultural University",
	"water resources": "BIT Mesra Water Systems Lab",
	"environment": "National University of Study and Research in Law",
	"public safety": "BIT Mesra Smart Mobility Lab",
	"societal innovation": "Ranchi University Innovation Centre",
}


def password_hash(password):
	return hashlib.sha256(password.encode("utf-8")).hexdigest()


def save_accounts():
	ACCOUNT_FILE.write_text(json.dumps(ACCOUNTS, indent=2), encoding="utf-8")


def send_otp_email(recipient, code):
	sender = os.environ.get("COMMON_GROUND_GMAIL")
	app_password = os.environ.get("COMMON_GROUND_GMAIL_APP_PASSWORD")
	if not sender or not app_password:
		raise RuntimeError("Gmail delivery is not configured. Set COMMON_GROUND_GMAIL and COMMON_GROUND_GMAIL_APP_PASSWORD.")
	message = EmailMessage()
	message["Subject"] = "Your Common Ground password reset code"
	message["From"] = sender
	message["To"] = recipient
	message.set_content(f"Your Common Ground password reset code is {code}. It expires when a new code is requested.")
	with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
		smtp.login(sender, app_password)
		smtp.send_message(message)


class PlatformHandler(BaseHTTPRequestHandler):
	def _send(self, status, body, content_type="application/json"):
		payload = body if isinstance(body, bytes) else body.encode("utf-8")
		self.send_response(status)
		self.send_header("Content-Type", f"{content_type}; charset=utf-8")
		self.send_header("Content-Length", str(len(payload)))
		self.send_header("Access-Control-Allow-Origin", "*")
		self.end_headers()
		self.wfile.write(payload)

	def _json(self):
		length = int(self.headers.get("Content-Length", 0))
		return json.loads(self.rfile.read(length) or b"{}")

	def do_OPTIONS(self):
		self.send_response(204)
		self.send_header("Access-Control-Allow-Origin", "*")
		self.send_header("Access-Control-Allow-Headers", "Content-Type")
		self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		self.end_headers()

	def do_GET(self):
		route = urlparse(self.path).path
		if route == "/api/challenges":
			self._send(200, json.dumps({"challenges": CHALLENGES}))
			return
		if route == "/api/network":
			self._send(200, json.dumps({
				"challenges": CHALLENGES,
				"certificates": CERTIFICATES,
				"roles": ["University", "Government"],
			}))
			return
		match = re.fullmatch(r"/api/challenges/(\d+)", route)
		if match:
			challenge = next((item for item in CHALLENGES if item["id"] == int(match.group(1))), None)
			self._send(200 if challenge else 404, json.dumps({"challenge": challenge} if challenge else {"error": "Challenge not found"}))
			return
		match = re.fullmatch(r"/api/challenges/(\d+)/activity", route)
		if match:
			challenge = next((item for item in CHALLENGES if item["id"] == int(match.group(1))), None)
			if not challenge:
				self._send(404, json.dumps({"error": "Challenge not found"}))
				return
			roles = ["Community contributor", "University researcher", "Industry mentor", "Local administrator", "Student designer"]
			collaborators = [{"name": f"{roles[index % len(roles)]} {index + 1:02d}", "role": roles[index % len(roles)]} for index in range(min(challenge["participants"], 5))]
			ideas = ACTIVITY.get(challenge["id"], [])
			if not ideas and challenge["ideas"]:
				ideas = [{"text": f"{challenge['ideas']} community ideas are currently being reviewed. Join this challenge to add your perspective.", "author": "Community activity", "time": challenge["time"]}]
			self._send(200, json.dumps({"challenge": challenge, "collaborators": collaborators, "ideas": ideas}))
			return
		if route == "/api/dashboard":
			domains = {}
			for challenge in CHALLENGES:
				domains[challenge["category"]] = domains.get(challenge["category"], 0) + 1
			self._send(200, json.dumps({
				"challenges": len(CHALLENGES),
				"collaborators": sum(item["participants"] for item in CHALLENGES),
				"ideas": sum(item["ideas"] for item in CHALLENGES),
				"districts": len({item["location"] for item in CHALLENGES}),
				"domains": domains,
				"milestones": 68,
				"active_partners": 24,
			}))
			return
		if route == "/" or route == "/landing.html":
			self._send(200, (ROOT / "landing.html").read_bytes(), "text/html")
			return
		if route == "/app":
			self._send(200, (ROOT / "app.html").read_bytes(), "text/html")
			return
		if route == "/index.html":
			self._send(200, (ROOT / "index.html").read_bytes(), "text/html")
			return
		if route in ("/how-it-works", "/how-it-works.html"):
			self._send(200, (ROOT / "how-it-works.html").read_bytes(), "text/html")
			return
		if route in ("/partners", "/partners.html"):
			self._send(200, (ROOT / "partners.html").read_bytes(), "text/html")
			return
		self._send(404, json.dumps({"error": "Not found"}))

	def do_POST(self):
		route = urlparse(self.path).path
		try:
			data = self._json()
		except (json.JSONDecodeError, ValueError):
			self._send(400, json.dumps({"error": "Please send valid JSON"}))
			return

		if route == "/api/auth/register":
			email = str(data.get("email", "")).strip().lower()
			password = str(data.get("password", ""))
			if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(password) < 6:
				self._send(400, json.dumps({"error": "Use a valid email and a password of at least 6 characters"}))
				return
			if email in ACCOUNTS:
				self._send(409, json.dumps({"error": "An account with this email already exists"}))
				return
			ACCOUNTS[email] = {"password": password_hash(password), "photo": data.get("photo", "")}
			save_accounts()
			self._send(201, json.dumps({"email": email, "photo": ACCOUNTS[email]["photo"], "message": "Account created"}))
			return

		if route == "/api/auth/login":
			ensure_demo_account()
			email = str(data.get("email", "")).strip().lower()
			password = str(data.get("password", ""))
			account = ACCOUNTS.get(email)
			if email == DEMO_EMAIL and password == DEMO_PASSWORD:
				account = ACCOUNTS[DEMO_EMAIL]
			elif not account or account.get("password") != password_hash(password):
				self._send(401, json.dumps({"error": "Email or password is incorrect"}))
				return
			self._send(200, json.dumps({"email": email, "photo": account["photo"], "message": "Signed in"}))
			return

		match = re.fullmatch(r"/api/auth/(google|apple)", route)
		if match:
			provider = match.group(1)
			client_id = os.environ.get(f"COMMON_GROUND_{provider.upper()}_CLIENT_ID")
			redirect_uri = os.environ.get("COMMON_GROUND_OAUTH_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/callback")
			if not client_id:
				ensure_demo_account()
				self._send(200, json.dumps({"email": DEMO_EMAIL, "photo": ACCOUNTS[DEMO_EMAIL].get("photo", ""), "message": f"Local {provider.title()} sign-in"}))
				return
			if provider == "google":
				auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + f"client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=openid%20email%20profile"
			else:
				auth_url = "https://appleid.apple.com/auth/authorize?" + f"client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=name%20email"
			self._send(200, json.dumps({"provider": provider, "auth_url": auth_url}))
			return

		if route == "/api/auth/forgot":
			email = str(data.get("email", "")).strip().lower()
			if email not in ACCOUNTS:
				self._send(404, json.dumps({"error": "No account found for that email"}))
				return
			code = f"{secrets.randbelow(1000000):06d}"
			try:
				send_otp_email(email, code)
			except (OSError, smtplib.SMTPException, RuntimeError) as error:
				self._send(503, json.dumps({"error": str(error)}))
				return
			RESET_CODES[email] = code
			self._send(200, json.dumps({"message": "OTP sent to your registered email"}))
			return

		if route == "/api/auth/reset":
			email = str(data.get("email", "")).strip().lower()
			if RESET_CODES.get(email) != str(data.get("otp", "")):
				self._send(400, json.dumps({"error": "That OTP is invalid or has expired"}))
				return
			password = str(data.get("password", ""))
			if len(password) < 6:
				self._send(400, json.dumps({"error": "Password must be at least 6 characters"}))
				return
			ACCOUNTS[email]["password"] = password_hash(password)
			save_accounts()
			del RESET_CODES[email]
			self._send(200, json.dumps({"email": email, "photo": ACCOUNTS[email]["photo"], "message": "Password updated"}))
			return

		if route == "/api/ai/solution":
			title = str(data.get("title", "")).strip()
			category = str(data.get("category", "community challenge")).strip()
			if not title:
				self._send(400, json.dumps({"error": "Choose a challenge first"}))
				return
			self._send(200, json.dumps({
				"solution": {
					"headline": f"A practical pilot for {title.lower()}",
					"steps": [
						f"Map the people, places, and constraints involved in this {category.lower()} challenge.",
						"Run a small two-week pilot with community members and one implementation partner.",
						"Measure reach, participation, cost, and feedback before expanding the approach.",
					],
					"partners": ["Community representatives", "University research team", "Local implementation partner"],
				}
			}))
			return

		if route == "/api/challenges":
			required = ["title", "summary", "category", "organization"]
			if any(not str(data.get(field, "")).strip() for field in required):
				self._send(400, json.dumps({"error": "Title, summary, category, and organization are required"}))
				return
			challenge = {
				"id": max(item["id"] for item in CHALLENGES) + 1,
				"title": data["title"].strip(), "summary": data["summary"].strip(),
				"category": data["category"].strip(), "stage": "Open for ideas",
				"organization": data["organization"].strip(), "organization_type": "Community partner",
				"location": data.get("location", "Remote"), "time": "just now", "participants": 1,
				"ideas": 0, "impact": "To be discovered", "tags": ["new challenge"], "featured": False,
				"evidence_files": data.get("evidence_files", []), "priority": data.get("priority", "Standard"),
				"recommended_university": UNIVERSITY_ROUTES.get(data["category"].strip().lower(), "Jharkhand University Innovation Network"),
			}
			CHALLENGES.insert(0, challenge)
			self._send(201, json.dumps({"challenge": challenge}))
			return

		match = re.fullmatch(r"/api/challenges/(\d+)/certificate", route)
		if match:
			challenge = next((item for item in CHALLENGES if item["id"] == int(match.group(1))), None)
			issuer = str(data.get("issuer", "")).strip()
			role = str(data.get("role", "")).strip()
			if not challenge:
				self._send(404, json.dumps({"error": "Challenge not found"}))
				return
			if not issuer or role not in ("University", "Government"):
				self._send(400, json.dumps({"error": "Choose a valid institution and role"}))
				return
			certificate = {
				"id": f"CERT-{challenge['id']}-{secrets.token_hex(3).upper()}",
				"challenge_id": challenge["id"], "challenge_title": challenge["title"],
				"issuer": issuer, "role": role, "issued_at": "just now",
				"recipient": challenge.get("organization", "Community contributor"),
			}
			CERTIFICATES[str(challenge["id"])] = certificate
			challenge["certificate"] = certificate
			self._send(201, json.dumps({"certificate": certificate}))
			return

		match = re.fullmatch(r"/api/challenges/(\d+)/(join|ideas)", route)
		if match:
			challenge = next((item for item in CHALLENGES if item["id"] == int(match.group(1))), None)
			if not challenge:
				self._send(404, json.dumps({"error": "Challenge not found"}))
				return
			if match.group(2) == "join":
				challenge["participants"] += 1
				self._send(200, json.dumps({"challenge": challenge, "message": "You joined this challenge"}))
				return
			idea = str(data.get("idea", "")).strip()
			if not idea:
				self._send(400, json.dumps({"error": "Idea is required"}))
				return
			challenge["ideas"] += 1
			ACTIVITY.setdefault(challenge["id"], []).append({"text": idea, "author": "You", "time": "just now"})
			self._send(201, json.dumps({"challenge": challenge, "message": "Idea added to the challenge"}))
			return
		self._send(404, json.dumps({"error": "Not found"}))

	def log_message(self, format, *args):
		return


if __name__ == "__main__":
	ensure_demo_account()
	port = 8000
	print(f"Common Ground is running at http://localhost:{port}")
	print(f"Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
	ThreadingHTTPServer(("0.0.0.0", port), PlatformHandler).serve_forever()
