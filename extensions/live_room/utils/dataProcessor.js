async function processProducts(data, sendProductsListToBackground) {
  return new Promise((resolve, reject) => {
    try {
      // 新增延时函数
      const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
      // 生成随机延时
      const getRandomDelay = () => Math.floor(Math.random() * 2000) + 3000;

      let productsList = data.info || [];
      console.log("待处理商品数量:", productsList.length);

      // 创建带延时的请求任务链
      const processProduct = async (productId) => {
        try {
          // 第一阶段请求
          console.log(`开始处理商品 ${productId} 的commodityDetail`);
          const commodityDetail = await getCommodityDetail(
            productId,
            productsList
          );
          const productIndex = productsList.findIndex(
            (p) => p.product_base_info.product_id === productId
          );
          if (productIndex > -1) {
            productsList[productIndex].commodity_info =
              commodityDetail.commodity_info || {};
            productsList[productIndex].use_rule_info =
              commodityDetail.use_rule_info || {};
          }
          await delay(getRandomDelay());

          // 第二阶段请求（增加间隔）
          console.log(`开始处理商品 ${productId} 的productDetail`);
          const productDetail = await getProductDetail(productId, productsList);
          if (productIndex > -1) {
            productsList[productIndex].product_info =
              productDetail.product_info || {};
            productsList[productIndex].poi_nearest =
              productDetail.poi_nearest || {};
          }
          await delay(getRandomDelay());
        } catch (error) {
          console.error(`商品 ${productId} 处理失败:`, error);
        }
      };

      let currentIndex = 0;
      let queueDelay = 0;
      productsList.forEach((product) => {
        const productId = product.product_base_info.product_id;
        const productName = product.product_base_info.name;

        setTimeout(() => {
          processProduct(productId).finally(async () => {
            currentIndex++;
            console.log(`商品 ${productName}处理完成 ...`);
            if (currentIndex >= productsList.length) {
              const res = await sendProductsListToBackground(productsList);
              console.log("发送商品数据到后台", res);
              resolve(res);
            }
          });
        }, queueDelay);
        queueDelay = getRandomDelay(); // 队列间隔递增
      });
    } catch (e) {
      console.error("处理数据失败:", e);
      reject(e);
    }
  });
}

function formatProductDetails(detailData) {
  if (!detailData || !detailData.detail_info) {
    return null;
  }

  const { product_format = [], detail_config = [] } = detailData.detail_info;

  const formatDetailConfig = detail_config.map((c) =>
    c.main_content.map((m) => m.title + "：" + m.content.join(","))
  );

  const formatDetailInfo = product_format.map((p) =>
    p.format.map((f) => f.name + "：" + f.message.map((m) => m.desc).join(","))
  );

  return {
    detail: detailData.detail_info,
    config: formatDetailConfig,
    info: formatDetailInfo,
  };
}
