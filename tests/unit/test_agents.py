import asyncio

import pytest

from marketing_swarm.agents import create_agent
from marketing_swarm.schemas.brief import CampaignBrief, TaskSpec


@pytest.mark.parametrize('agent_slug', [
    'supervisor',
    'market_research',
    'competitive_intelligence',
    'content_strategy',
    'copywriter',
    'seo_geo',
    'social_media',
    'email_marketing',
    'creative_brief',
    'brand_voice_qa',
    'analytics_optimization',
])
def test_agent_runs(agent_slug):
    brief = CampaignBrief.from_text('Launch a practical campaign for remote operations teams with proof and clear action.')
    task = TaskSpec(title='agent task', description='Create audience message cta artifact', agent=agent_slug)
    result = asyncio.run(create_agent(agent_slug).run(brief, task, {'documents': [{'title': 'proof', 'text': 'audience message cta proof', 'source': 'test'}]}))
    assert result.agent == agent_slug
    assert result.assets
    assert result.confidence.value > 0.5
