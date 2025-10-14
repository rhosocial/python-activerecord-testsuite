# 电商系统 - 客户购买流程测试实施方案

## 测试目标

验证完整的客户购买流程，包括用户注册、产品浏览、购物车管理、订单创建、支付处理和订单跟踪等核心电商功能。

## Provider 接口扩展

### IEcommerceProvider 接口方法

```python
from abc import ABC, abstractmethod
from typing import Type, Tuple, List, Dict
from rhosocial.activerecord import ActiveRecord

class IEcommerceProvider(ABC):
    """电商系统测试数据提供者接口"""
    
    @abstractmethod
    def setup_ecommerce_models(self, scenario: str) -> Tuple[
        Type[ActiveRecord],  # User
        Type[ActiveRecord],  # Product
        Type[ActiveRecord],  # Category
        Type[ActiveRecord],  # Cart
        Type[ActiveRecord],  # CartItem
        Type[ActiveRecord],  # Order
        Type[ActiveRecord],  # OrderItem
        Type[ActiveRecord],  # Payment
        Type[ActiveRecord],  # Shipping
        Type[ActiveRecord]   # Review
    ]:
        """设置所有电商模型"""
        pass
    
    @abstractmethod
    def create_sample_catalog(
        self, 
        category_count: int,
        products_per_category: int
    ) -> List[Dict]:
        """创建示例产品目录"""
        pass
    
    @abstractmethod
    def create_test_users(
        self,
        customer_count: int,
        staff_count: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """创建测试用户（客户和员工）"""
        pass
    
    @abstractmethod
    def cleanup_ecommerce_data(self, scenario: str):
        """清理电商测试数据"""
        pass
```

## 必要的夹具定义

### 基础模型夹具

```python
@pytest.fixture
def ecommerce_models(request):
    """提供所有电商模型"""
    scenario = request.config.getoption("--scenario", default="local")
    provider = get_ecommerce_provider()
    
    models = provider.setup_ecommerce_models(scenario)
    yield models
    
    provider.cleanup_ecommerce_data(scenario)

@pytest.fixture
def User(ecommerce_models):
    """用户模型"""
    return ecommerce_models[0]

@pytest.fixture
def Product(ecommerce_models):
    """产品模型"""
    return ecommerce_models[1]

@pytest.fixture
def Category(ecommerce_models):
    """分类模型"""
    return ecommerce_models[2]

@pytest.fixture
def Cart(ecommerce_models):
    """购物车模型"""
    return ecommerce_models[3]

@pytest.fixture
def CartItem(ecommerce_models):
    """购物车项目模型"""
    return ecommerce_models[4]

@pytest.fixture
def Order(ecommerce_models):
    """订单模型"""
    return ecommerce_models[5]

@pytest.fixture
def OrderItem(ecommerce_models):
    """订单项目模型"""
    return ecommerce_models[6]

@pytest.fixture
def Payment(ecommerce_models):
    """支付模型"""
    return ecommerce_models[7]

@pytest.fixture
def Shipping(ecommerce_models):
    """配送模型"""
    return ecommerce_models[8]

@pytest.fixture
def Review(ecommerce_models):
    """评价模型"""
    return ecommerce_models[9]
```

### 测试数据夹具

```python
@pytest.fixture
def sample_catalog(request, ecommerce_models):
    """示例产品目录"""
    provider = get_ecommerce_provider()
    scenario = request.config.getoption("--scenario", default="local")
    
    catalog = provider.create_sample_catalog(
        category_count=5,
        products_per_category=10
    )
    return catalog

@pytest.fixture
def test_customer(User):
    """测试客户用户"""
    customer = User(
        username="test_customer",
        email="customer@test.com",
        user_type="customer",
        is_active=True
    )
    customer.save()
    return customer

@pytest.fixture
def test_products(Product, Category, sample_catalog):
    """测试产品列表"""
    products = []
    for product_data in sample_catalog[:5]:  # 取前5个产品
        product = Product(**product_data)
        product.save()
        products.append(product)
    return products
```

## 测试类和函数签名

### TestCustomerRegistration - 客户注册测试

```python
class TestCustomerRegistration:
    """客户注册流程测试"""
    
    def test_register_new_customer(self, User):
        """测试新客户注册"""
        pass
    
    def test_register_with_invalid_email(self, User):
        """测试无效邮箱注册（应失败）"""
        pass
    
    def test_register_duplicate_username(self, User, test_customer):
        """测试重复用户名注册（应失败）"""
        pass
    
    def test_register_with_validation(self, User):
        """测试带字段验证的注册"""
        pass
```

### TestProductBrowsing - 产品浏览测试

```python
class TestProductBrowsing:
    """产品浏览功能测试"""
    
    def test_list_all_products(self, Product, test_products):
        """测试列出所有产品"""
        pass
    
    def test_filter_by_category(self, Product, Category, test_products):
        """测试按分类筛选产品"""
        pass
    
    def test_search_products_by_name(self, Product, test_products):
        """测试按名称搜索产品"""
        pass
    
    def test_filter_by_price_range(self, Product, test_products):
        """测试按价格范围筛选"""
        pass
    
    def test_product_pagination(self, Product, test_products):
        """测试产品分页"""
        pass
```

### TestCartManagement - 购物车管理测试

```python
class TestCartManagement:
    """购物车管理测试"""
    
    def test_create_cart(self, Cart, test_customer):
        """测试创建购物车"""
        pass
    
    def test_add_item_to_cart(self, Cart, CartItem, test_customer, test_products):
        """测试添加商品到购物车"""
        pass
    
    def test_update_cart_item_quantity(self, Cart, CartItem, test_customer, test_products):
        """测试更新购物车商品数量"""
        pass
    
    def test_remove_item_from_cart(self, Cart, CartItem, test_customer, test_products):
        """测试从购物车移除商品"""
        pass
    
    def test_clear_cart(self, Cart, CartItem, test_customer, test_products):
        """测试清空购物车"""
        pass
    
    def test_cart_total_calculation(self, Cart, CartItem, test_customer, test_products):
        """测试购物车总价计算"""
        pass
```

### TestInventoryChecking - 库存检查测试

```python
class TestInventoryChecking:
    """库存检查测试"""
    
    def test_check_product_availability(self, Product, test_products):
        """测试检查产品可用性"""
        pass
    
    def test_add_to_cart_with_insufficient_stock(self, Cart, CartItem, Product, test_customer):
        """测试库存不足时添加到购物车（应失败）"""
        pass
    
    def test_reserve_inventory_on_add_to_cart(self, Product, Cart, CartItem, test_customer):
        """测试添加到购物车时预留库存"""
        pass
    
    def test_release_inventory_on_cart_clear(self, Product, Cart, CartItem, test_customer):
        """测试清空购物车时释放库存"""
        pass
```

### TestOrderCreation - 订单创建测试

```python
class TestOrderCreation:
    """订单创建测试"""
    
    def test_create_order_from_cart(
        self, 
        Order, 
        OrderItem, 
        Cart, 
        CartItem,
        test_customer, 
        test_products
    ):
        """测试从购物车创建订单"""
        pass
    
    def test_order_number_generation(self, Order, test_customer):
        """测试订单号生成"""
        pass
    
    def test_order_total_calculation(
        self, 
        Order, 
        OrderItem,
        test_customer, 
        test_products
    ):
        """测试订单总价计算"""
        pass
    
    def test_atomic_cart_to_order_conversion(
        self,
        Order,
        OrderItem,
        Cart,
        CartItem,
        Product,
        test_customer,
        test_products
    ):
        """测试购物车到订单的原子转换（事务性）"""
        pass
    
    def test_inventory_deduction_on_order(
        self,
        Order,
        OrderItem,
        Product,
        test_customer,
        test_products
    ):
        """测试下单时扣减库存"""
        pass
```

### TestPaymentProcessing - 支付处理测试

```python
class TestPaymentProcessing:
    """支付处理测试"""
    
    def test_create_payment(self, Payment, Order, test_customer, test_products):
        """测试创建支付记录"""
        pass
    
    def test_successful_payment(self, Payment, Order, test_customer):
        """测试成功支付"""
        pass
    
    def test_failed_payment(self, Payment, Order, test_customer):
        """测试支付失败"""
        pass
    
    def test_payment_status_update(self, Payment, Order, test_customer):
        """测试支付状态更新"""
        pass
    
    def test_order_status_after_payment(self, Payment, Order, test_customer):
        """测试支付后订单状态"""
        pass
```

### TestOrderTracking - 订单跟踪测试

```python
class TestOrderTracking:
    """订单跟踪测试"""
    
    def test_get_order_status(self, Order, test_customer, test_products):
        """测试获取订单状态"""
        pass
    
    def test_list_customer_orders(self, Order, test_customer, test_products):
        """测试列出客户所有订单"""
        pass
    
    def test_order_status_history(self, Order, test_customer):
        """测试订单状态历史"""
        pass
    
    def test_track_order_by_number(self, Order, test_customer):
        """测试通过订单号跟踪订单"""
        pass
```

### TestShippingManagement - 配送管理测试

```python
class TestShippingManagement:
    """配送管理测试"""
    
    def test_create_shipping_address(self, Shipping, test_customer):
        """测试创建配送地址"""
        pass
    
    def test_assign_shipping_to_order(self, Shipping, Order, test_customer, test_products):
        """测试为订单分配配送地址"""
        pass
    
    def test_update_shipping_address(self, Shipping, Order, test_customer):
        """测试更新配送地址"""
        pass
    
    def test_multiple_shipping_addresses(self, Shipping, test_customer):
        """测试管理多个配送地址"""
        pass
```

## 功能覆盖范围

### 核心功能

1. **用户管理**
   - 客户注册与验证
   - 用户认证
   - 用户类型区分（客户/员工）

2. **产品管理**
   - 产品列表展示
   - 分类筛选
   - 搜索功能
   - 价格范围筛选
   - 分页支持

3. **购物车**
   - 购物车创建
   - 商品添加/更新/删除
   - 购物车清空
   - 总价计算
   - 库存检查与预留

4. **库存管理**
   - 可用性检查
   - 库存预留
   - 库存释放
   - 库存扣减

5. **订单处理**
   - 订单创建
   - 订单号生成
   - 购物车到订单转换（事务性）
   - 订单总价计算
   - 订单状态管理

6. **支付处理**
   - 支付记录创建
   - 支付状态更新
   - 支付成功/失败处理
   - 订单状态联动

7. **订单跟踪**
   - 订单状态查询
   - 订单列表
   - 订单历史
   - 订单号跟踪

8. **配送管理**
   - 配送地址管理
   - 订单配送分配
   - 地址更新
   - 多地址支持

### 所需能力（Capabilities）

- **事务支持**：购物车到订单转换的原子性
- **关系加载**：订单->订单项->产品的嵌套加载
- **聚合计算**：总价计算、库存统计
- **查询构建**：复杂的产品筛选、订单查询
- **并发控制**：库存扣减的并发安全（如需要）

### 测试数据规模

- 用户：10-50 个测试用户
- 产品：50-100 个产品，5-10 个分类
- 订单：每个测试场景 1-10 个订单
- 购物车：每个客户 1 个活动购物车

### 性能预期

- 产品列表查询：< 100ms（100个产品）
- 购物车操作：< 50ms
- 订单创建：< 200ms（包含事务）
- 支付处理：< 100ms
