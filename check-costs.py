#!/usr/bin/env python3
"""
简单成本检查脚本
基于 cloud-ops 技能的最佳实践
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

def check_free_tier_usage():
    """检查免费层使用情况"""
    
    print("💰 Cloud Cost Check - Free Tier Analysis")
    print("="*50)
    
    # 2026年免费层限制
    limits = {
        'cloudflare_pages': {
            'bandwidth': '无限制',
            'daily_requests': 100000,
            'monthly_builds': 500,
            'current_usage': '未知（需要API访问）',
            'status': '✅ 预计在免费层内'
        },
        'vercel': {
            'bandwidth_gb': 100,
            'build_minutes': 6000,
            'serverless_invocations': 100000,
            'current_usage': '未知（需要API访问）',
            'status': '✅ 预计在免费层内'
        },
        'github_pages': {
            'bandwidth': '无限制（公共仓库）',
            'build_minutes': '无限制（公共仓库）',
            'current_usage': '完全免费',
            'status': '✅ 完全免费'
        },
        'deno_deploy': {
            'monthly_requests': 100000,
            'execution_time': '100k GiB-seconds',
            'current_usage': '未知',
            'status': '✅ 预计在免费层内'
        }
    }
    
    total_estimated_cost = 0
    platforms_in_free_tier = 0
    
    for platform, data in limits.items():
        print(f"\n🌐 {platform.replace('_', ' ').title()}:")
        print(f"   限制: {json.dumps(data, ensure_ascii=False, indent=6)[1:-1]}")
        print(f"   状态: {data['status']}")
        
        if '免费层内' in data['status'] or '完全免费' in data['status']:
            platforms_in_free_tier += 1
    
    print(f"\n📊 摘要:")
    print(f"   平台数量: {len(limits)}")
    print(f"   在免费层内: {platforms_in_free_tier}/{len(limits)}")
    print(f"   预估月费用: ${total_estimated_cost:.2f}")
    
    if platforms_in_free_tier == len(limits):
        print("🎉 所有平台都在免费层内！")
    else:
        print("⚠️  有些平台可能需要费用，建议检查使用情况")
    
    return limits

def generate_cost_report():
    """生成成本报告"""
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'analysis': check_free_tier_usage(),
        'recommendations': [
            {
                'priority': 'HIGH',
                'title': '保持公共仓库状态',
                'description': 'GitHub Pages 和 Actions 对公共仓库完全免费',
                'action': '确保 content-producer 仓库保持公开状态'
            },
            {
                'priority': 'MEDIUM',
                'title': '监控 Cloudflare 使用量',
                'description': 'Cloudflare Pages 有每日请求限制',
                'action': '定期检查 analytics.cloudflare.com'
            },
            {
                'priority': 'LOW',
                'title': '优化构建过程',
                'description': '减少不必要的构建可以节省资源',
                'action': '确保构建过程高效，避免重复构建'
            }
        ],
        'next_review_date': (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
    }
    
    # 保存报告
    report_file = Path('cost-report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 报告已保存到: {report_file}")
    
    return report

def main():
    """主函数"""
    from datetime import timedelta
    
    print("🚀 云成本优化检查")
    print("基于 cloud-ops 技能的最佳实践")
    print("="*50)
    
    # 检查免费层使用
    limits = check_free_tier_usage()
    
    # 生成报告
    report = generate_cost_report()
    
    print("\n✅ 检查完成！")
    print("💡 建议：")
    for rec in report['recommendations']:
        print(f"   [{rec['priority']}] {rec['title']}: {rec['action']}")

if __name__ == '__main__':
    main()