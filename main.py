import os

import tests

def main():
    if os.getcwd().endswith('src') is False:
        os.chdir('./src')
    
    # tests.test_collector_from_html()
    # tests.test_collector_to_json()
    # tests.test_scraper()
    # tests.test_document_builder()
    # tests.test_clean_documents()
    from controllers import classifier

if __name__ == '__main__':
    main()