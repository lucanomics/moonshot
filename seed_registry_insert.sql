INSERT INTO source_registry
(site_name, source_type, seed_url, official_domain, parser_name, crawl_interval_hours, priority)
VALUES
('Hi Korea', 'service', 'https://www.hikorea.go.kr/cvlappl/CvlapplStep1.pt?locale=ko', 'www.hikorea.go.kr', 'hikorea_service_parser', 24, 10),
('Korea Immigration Service', 'html', 'https://www.immigration.go.kr/immigration_eng/index.do', 'www.immigration.go.kr', 'immigration_home_parser', 24, 20),
('MOJ Guide PDF', 'pdf', 'https://www.immigration.go.kr/bbs/immigration/47/426385/download.do', 'www.immigration.go.kr', 'immigration_pdf_parser', 24, 30);
