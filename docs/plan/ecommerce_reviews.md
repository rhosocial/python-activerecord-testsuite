# 电商系统 - 评价系统测试实施方案

## 测试目标

验证产品评价和评分系统，包括评价提交、评分聚合、评价审核、有用投票和评价分页展示等功能。

## Provider 接口扩展

### IReviewProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class IReviewProvider(ABC):
    """评价系统测试数据提供者接口"""
    
    @abstractmethod
    def setup_review_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Product
        Type[ActiveRecord],  # Review
        Type[ActiveRecord],  # Rating
        Type[ActiveRecord],  # ReviewVote
        Type[ActiveRecord]   # ReviewImage
    ]:
        """设置评价系统相关模型"""
        pass
    
    @abstractmethod
    def create_test_reviews(
        self,
        user_count: int,
        reviews_per_user_range: Tuple[int, int]
    ) -> List[Dict]:
        """创建测试评价"""
        pass
    
    @abstractmethod
    def create_sample_products(
        self,
        product_count: int
    ) -> List[Dict]:
        """创建示例产品"""
        pass
```

## 必要的夹具定义

```python
@pytest.fixture
def review_models(request):
    """提供评价系统模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_review_provider()
    
    models = provider.setup_review_models(scenario)
    yield models
    
    provider.cleanup_review_data(scenario)

@pytest.fixture
def User(review_models):
    """用户模型"""
    return review_models[0]

@pytest.fixture
def Product(review_models):
    """产品模型"""
    return review_models[1]

@pytest.fixture
def Review(review_models):
    """评价模型"""
    return review_models[2]

@pytest.fixture
def Rating(review_models):
    """评分模型"""
    return review_models[3]

@pytest.fixture
def ReviewVote(review_models):
    """评价投票模型"""
    return review_models[4]

@pytest.fixture
def ReviewImage(review_models):
    """评价图片模型"""
    return review_models[5]

@pytest.fixture
def test_user(User):
    """测试用户"""
    user = User(
        username="test_reviewer",
        email="reviewer@test.com",
        is_active=True
    )
    user.save()
    return user

@pytest.fixture
def test_product(Product):
    """测试产品"""
    product = Product(
        name="Test Product",
        price=99.99,
        is_active=True
    )
    product.save()
    return product

@pytest.fixture
def test_reviews(request, Review, test_user, test_product):
    """测试评价数据"""
    provider = get_review_provider()
    reviews = provider.create_test_reviews(
        user_count=10,
        reviews_per_user_range=(1, 3)
    )
    return reviews
```

## 测试类和函数签名

### TestReviewSubmission - 评价提交测试

```python
class TestReviewSubmission:
    """评价提交测试"""
    
    def test_submit_review(self, Review, test_user, test_product):
        """测试提交评价"""
        pass
    
    def test_submit_review_with_rating(self, Review, Rating, test_user, test_product):
        """测试提交带评分的评价"""
        pass
    
    def test_submit_review_with_images(self, Review, ReviewImage, test_user, test_product):
        """测试提交带图片的评价"""
        pass
    
    def test_review_validation(self, Review, test_user, test_product):
        """测试评价内容验证"""
        pass
    
    def test_duplicate_review_prevention(self, Review, test_user, test_product):
        """测试防止重复评价"""
        pass
    
    def test_review_without_purchase(self, Review, User, Product):
        """测试未购买用户评价（应失败）"""
        pass
```

### TestRatingSystem - 评分系统测试

```python
class TestRatingSystem:
    """评分系统测试"""
    
    def test_submit_rating(self, Rating, test_user, test_product):
        """测试提交评分"""
        pass
    
    def test_rating_range_validation(self, Rating, test_user, test_product):
        """测试评分范围验证（1-5星）"""
        pass
    
    def test_update_rating(self, Rating, test_user, test_product):
        """测试更新评分"""
        pass
    
    def test_rating_without_review(self, Rating, test_user, test_product):
        """测试单独评分（无评价文字）"""
        pass
```

### TestRatingAggregation - 评分聚合测试

```python
class TestRatingAggregation:
    """评分聚合测试"""
    
    def test_calculate_average_rating(self, Product, Rating, test_reviews):
        """测试计算平均评分"""
        pass
    
    def test_rating_distribution(self, Product, Rating, test_reviews):
        """测试评分分布统计"""
        pass
    
    def test_total_review_count(self, Product, Review, test_reviews):
        """测试评价总数统计"""
        pass
    
    def test_rating_percentages(self, Product, Rating, test_reviews):
        """测试各星级百分比"""
        pass
    
    def test_verified_purchase_rating(self, Product, Rating, Review):
        """测试已验证购买评分统计"""
        pass
```

### TestReviewModeration - 评价审核测试

```python
class TestReviewModeration:
    """评价审核测试"""
    
    def test_pending_review_queue(self, Review, test_reviews):
        """测试待审核评价队列"""
        pass
    
    def test_approve_review(self, Review, test_user, test_product):
        """测试批准评价"""
        pass
    
    def test_reject_review(self, Review, test_user, test_product):
        """测试拒绝评价"""
        pass
    
    def test_flag_inappropriate_review(self, Review, User, test_product):
        """测试标记不当评价"""
        pass
    
    def test_bulk_approve_reviews(self, Review, test_reviews):
        """测试批量批准评价"""
        pass
    
    def test_moderation_notes(self, Review, test_user, test_product):
        """测试审核备注"""
        pass
```

### TestReviewVoting - 评价投票测试

```python
class TestReviewVoting:
    """评价投票测试"""
    
    def test_vote_helpful(self, Review, ReviewVote, User, test_product):
        """测试投"有用"票"""
        pass
    
    def test_vote_not_helpful(self, Review, ReviewVote, User, test_product):
        """测试投"无用"票"""
        pass
    
    def test_change_vote(self, Review, ReviewVote, User, test_product):
        """测试更改投票"""
        pass
    
    def test_remove_vote(self, Review, ReviewVote, User, test_product):
        """测试移除投票"""
        pass
    
    def test_vote_count(self, Review, ReviewVote, test_reviews):
        """测试投票计数"""
        pass
    
    def test_prevent_self_voting(self, Review, ReviewVote, test_user, test_product):
        """测试防止自己给自己投票"""
        pass
```

### TestReviewDisplay - 评价展示测试

```python
class TestReviewDisplay:
    """评价展示测试"""
    
    def test_list_product_reviews(self, Review, Product, test_reviews):
        """测试列出产品评价"""
        pass
    
    def test_sort_by_date(self, Review, test_product, test_reviews):
        """测试按日期排序"""
        pass
    
    def test_sort_by_rating(self, Review, Rating, test_product, test_reviews):
        """测试按评分排序"""
        pass
    
    def test_sort_by_helpfulness(self, Review, ReviewVote, test_product, test_reviews):
        """测试按有用度排序"""
        pass
    
    def test_filter_by_rating(self, Review, Rating, test_product, test_reviews):
        """测试按评分筛选"""
        pass
    
    def test_verified_purchase_badge(self, Review, test_product):
        """测试已验证购买标识"""
        pass
```

### TestReviewPagination - 评价分页测试

```python
class TestReviewPagination:
    """评价分页测试"""
    
    def test_paginate_reviews(self, Review, test_product, test_reviews):
        """测试评价分页"""
        pass
    
    def test_page_size_control(self, Review, test_product, test_reviews):
        """测试分页大小控制"""
        pass
    
    def test_large_review_set(self, Review, Product):
        """测试大量评价分页性能"""
        pass
    
    def test_cursor_based_pagination(self, Review, test_product, test_reviews):
        """测试基于游标的分页"""
        pass
```

### TestReviewImages - 评价图片测试

```python
class TestReviewImages:
    """评价图片测试"""
    
    def test_upload_review_image(self, ReviewImage, Review, test_user, test_product):
        """测试上传评价图片"""
        pass
    
    def test_multiple_images(self, ReviewImage, Review, test_user, test_product):
        """测试多张图片"""
        pass
    
    def test_image_validation(self, ReviewImage, Review, test_user, test_product):
        """测试图片验证（格式、大小）"""
        pass
    
    def test_remove_review_image(self, ReviewImage, Review):
        """测试删除评价图片"""
        pass
```

### TestReviewStatistics - 评价统计测试

```python
class TestReviewStatistics:
    """评价统计测试"""
    
    def test_review_summary(self, Product, Review, Rating, test_reviews):
        """测试评价摘要统计"""
        pass
    
    def test_recent_review_trend(self, Product, Review, Rating):
        """测试近期评价趋势"""
        pass
    
    def test_reviewer_statistics(self, User, Review):
        """测试评价者统计"""
        pass
    
    def test_top_rated_products(self, Product, Rating):
        """测试最高评分产品"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **评价提交**
   - 评价提交
   - 带评分提交
   - 带图片提交
   - 内容验证
   - 重复防止
   - 购买验证

2. **评分系统**
   - 评分提交
   - 范围验证
   - 评分更新
   - 单独评分

3. **评分聚合**
   - 平均评分
   - 评分分布
   - 评价计数
   - 星级百分比
   - 验证购买统计

4. **评价审核**
   - 待审核队列
   - 批准/拒绝
   - 不当标记
   - 批量审核
   - 审核备注

5. **评价投票**
   - 有用投票
   - 无用投票
   - 投票更改
   - 投票移除
   - 投票计数
   - 自投防止

6. **评价展示**
   - 评价列表
   - 日期排序
   - 评分排序
   - 有用度排序
   - 评分筛选
   - 验证标识

7. **评价分页**
   - 分页展示
   - 分页大小
   - 大数据集性能
   - 游标分页

8. **评价图片**
   - 图片上传
   - 多图支持
   - 图片验证
   - 图片删除

9. **评价统计**
   - 评价摘要
   - 趋势分析
   - 评价者统计
   - 高分产品

### 所需能力（Capabilities）

- **聚合函数**：平均评分、评分分布统计
- **关系加载**：评价->用户、评价->产品、评价->投票
- **分页支持**：大量评价的分页展示
- **查询构建**：复杂的评价筛选和排序

### 测试数据规模

- 用户：10-50 个评价者
- 产品：10-30 个产品
- 评价：每个产品 5-100 条评价
- 评价图片：20-30% 的评价带图片
- 投票：每条评价 0-50 个投票

### 性能预期

- 评价提交：< 100ms
- 评分聚合计算：< 50ms（100条评价）
- 评价列表查询：< 100ms（分页20条）
- 大数据集分页：< 200ms（1000条评价）
- 评价统计查询：< 300ms
