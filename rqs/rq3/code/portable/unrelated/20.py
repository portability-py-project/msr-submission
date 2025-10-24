import re
import csv
from collections import defaultdict
from typing import List, Dict


class LogAnalyzer:
    def __init__(self):
        self.log_patterns = {
            'error': re.compile(r'\[ERROR\].*'),
            'warning': re.compile(r'\[WARNING\].*'),
            'info': re.compile(r'\[INFO\].*'),
            'timestamp': re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
        }
        self.stats = defaultdict(int)
    
    def parse_log_line(self, line: str) -> Dict:
        """Parse a single log line and extract information"""
        result = {'level': 'unknown', 'timestamp': None, 'message': line.strip()}
        
        for level, pattern in self.log_patterns.items():
            if level != 'timestamp' and pattern.search(line):
                result['level'] = level
                break
        
        timestamp_match = self.log_patterns['timestamp'].search(line)
        if timestamp_match:
            result['timestamp'] = timestamp_match.group()
        
        return result
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a log file and return statistics"""
        self.stats.clear()
        error_messages = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parsed = self.parse_log_line(line)
                self.stats[parsed['level']] += 1
                
                if parsed['level'] == 'error':
                    error_messages.append({
                        'line': line_num,
                        'timestamp': parsed['timestamp'],
                        'message': parsed['message']
                    })
        
        return {
            'total_lines': sum(self.stats.values()),
            'by_level': dict(self.stats),
            'error_rate': self.stats['error'] / sum(self.stats.values()) * 100,
            'recent_errors': error_messages[-5:]  # Last 5 errors
        }
    
    def export_summary(self, analysis: Dict, output_file: str):
        """Export analysis summary to CSV"""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Lines', analysis['total_lines']])
            writer.writerow(['Error Rate %', f"{analysis['error_rate']:.2f}"])
            
            for level, count in analysis['by_level'].items():
                writer.writerow([f'{level.title()} Count', count])


def generate_sample_log(file_path: str):
    """Generate a sample log file for testing"""
    import datetime
    
    log_entries = [
        "[INFO] Application started successfully",
        "[WARNING] Database connection slow",
        "[ERROR] Failed to process user request",
        "[INFO] Processing batch job",
        "[ERROR] Memory allocation failed"
    ]
    
    with open(file_path, 'w') as f:
        for i, entry in enumerate(log_entries):
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} {entry}\n")


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    
    generate_sample_log("sample.log")
    analysis = analyzer.analyze_file("sample.log")
    
    print(f"Total lines: {analysis['total_lines']}")
    print(f"Error rate: {analysis['error_rate']:.2f}%")
    print(f"Errors: {analysis['by_level']['error']}")
    
    analyzer.export_summary(analysis, "log_summary.csv")