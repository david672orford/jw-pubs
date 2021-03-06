from jwfetcher import Fetcher
from urllib.parse import urljoin, quote
import re

# Search for publications on JW.ORG.
class JWPubs(Fetcher):
	base_url = "https://www.jw.org/ru/"

	# Perform the search. Each returned item:
	# * Name of publication
	# * Name if issue
	# * URL of page on JW.ORG
	# * URL of thumbnail image
	def search(self, path, query):

		base_url = self.base_url
		page_href = quote(path)

		pubs = []
		while True:
			html = self.get_html(urljoin(base_url, page_href), query)
			#self.dump_html(html)

			base = html.xpath(".//base")
			if len(base) > 0:
				#print("base:", base[0].attrib)
				base_url = urljoin(base_url, base[0].attrib['href'])

			container = html.get_element_by_id('pubsViewResults')

			h2 = container.xpath("./h2")
			if len(h2) > 0:
				periodical_name = h2[0].text
			else:
				h1 = html.xpath(".//h1")
				if len(h1) > 0:
					periodical_name = h1[0].text
				else:
					periodical_name = None

			for pub in container.find_class('synopsis'):
				if "textOnly" in pub.attrib['class']:
					continue
				#self.dump_html(pub)

				m = re.search(r" pub-(\S+) ", pub.attrib['class'])
				assert m
				code = m.group(1)

				# Each synopsis contains two <div>s. The first contains a thumbnail image
				# linked to the HTML version of the publication.
				syn_image = pub.find_class('syn-img')[0]
				image_link = syn_image.xpath(".//a")[0]
				href = urljoin(self.base_url, image_link.attrib['href'])
				thumbnail = urljoin(self.base_url, image_link.xpath(".//img/@src")[0])

				# The second <div> contains the name of the publication and links
				# to more versions of it.
				syn_body = pub.find_class('syn-body')[0]
				name = syn_body.find_class('publicationDesc')[0].text_content().strip()

				# Periodicals will have a periodical name, an issue title, and an issue date.
				if periodical_name is not None and " iss-" in pub.attrib['class']:
					m = re.search(r" iss-(\S+) ", pub.attrib['class'])
					issue_code = m.group(1)
					pubs.append(dict(
						name = periodical_name,
						issue = name,
						code = code,
						issue_code = issue_code,
						href = href,
						thumbnail = thumbnail
						))
				else:
					pubs.append(dict(
						name = name,
						code = code,
						href = href,
						thumbnail = thumbnail
					))

			# If there are more pages of results, load the next one.
			pagination = html.find_class("pagination")
			if pagination:
				next_link = pagination[0].find_class("iconNext")
				if len(next_link) > 0:
					page_href = next_link[0].attrib['href']
					query = None
					continue

			# No more pages
			break

		return pubs

