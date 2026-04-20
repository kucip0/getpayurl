
$(document).ready(function(){
    let wholesale_discount_list = {};
    let reach_list = {};
    let contact_limit = {};
    var page = 1,limit = 30;
    var loading ;
    var flow ;
    let ka_page = 1;
    let ka_is_page = true;
    let ka_start_num = 0;
    let api_url = '';
    let toggle = true;
    let service ;
    $('body').on('click','.payType li',function(){
        let goodsId = $("#GoodsId").val();

        if(goodsId <= 0){
            return layer.msg('请先选择商品');
        }
        if($(this).attr('data-ident') === 'BalancePay'){
            $(".yue").hide();
            $("#is_dk").val(0);
            $("#switchDk").val(0);
            $("#switchDk").prop("checked",false);
            layui.form.render("checkbox");
            $("#ppp").html('余额支付 : ');
        }else if($(this).attr('data-id') !== 'BalancePay' && Number($("#umoney").val()) > 0 ){

            if($("#balance_deduction").val() == 1){
                let pay_first = $("#pay_first").val();
                if(pay_first == 1){
                    $("#is_dk").val(0);
                    $("#switchDk").val(0);
                    $("#switchDk").prop("checked",false);
                    $("#pay_first").val(0)
                }else {
                    $("#is_dk").val(1);
                    $("#switchDk").val(1);
                    $("#switchDk").prop("checked",true);
                }

                layui.form.render("checkbox");
                $(".yue").show();
                $("#ppp").html('在线支付 : ');
            }else{
                $("#is_dk").val(0);
                $("#switchDk").val(0);
                $("#switchDk").prop("checked",false);
                $("#dkPrice").val(0);
                $(".yue").hide();
                layui.form.render("checkbox");
                $("#ppp").html('在线支付 : ');
            }

        }else {
            $("#dkPrice").val(0);
            $(".yue").hide();
            $("#ppp").html('在线支付 : ');
        }
        if($("#fee_payer").val() == 2){
            $(".rate").show();
        }


        if( !$(this).hasClass('paySelect')){
            let id =  $(this).attr('data-id');
            let type =  $(this).attr('data-type');
            $('.payType li').removeClass('paySelect');
            $(this).addClass('paySelect');
            $("#payId").val(id);
            $("#payType").val(type);
        }
        calculation();
    });
    $('body').on('click','#shop_chats',function(){
        let area = [];
        let title = '客服服务中心';
        let url = $(this).attr('data-url');
        if($("#isMobile").val() == 1){
            area = ['100%', '100%'];
        }else {
            area =['650px', '780px'];
        }
        service = layer.open({
            type: 2,
            skin:'layui-layer-molv',
            shadeClose: false,
            shade: 0,
            resize:true,
            offset: 'rb',
            closeBtn : true,

            anim: 4,
            // zIndex:9999999999,
            content: url,
            area: area,
            title: title,
            btn: false,
        });
    });

    $('body').on('click','.cat ul li',function(){
        if( !$(this).hasClass('select')){
            $('.cat ul li').removeClass('select');
            $(this).addClass('select');
            let catId = $(this).attr('data-id');
            $("#cateId").val(catId);
            $("#goodsName").val('');
            $("#is_xh").val(0);
            $("#vip_goods").val(0);
            $(".goodsName").html('尚未选择商品');
            $(".goodsInfo").html('未选中商品');
            $('#quantity').removeAttr('disabled');
            $("#jiaose_box").hide();
            $("#GoodsId").val(0);
            $("#price").html(0);
            $("#coupon_type").val(1);
            $("#coupon_denomination").val(0);
            $("#songNum").val(0);
            $("#fee_payer").val(1);
            $("#kami_id").val('');
            $("#is_xh").val(0);
            $("#goodsPrice").val(0);
            $("#xhPrice").val(0);
            $("#kucun").html(0);
            $("#cards_stock_count").val(0);
            $("#card_password").hide();
            $(".smsPrice").html( $("#sms_payer").val());
            $("#sms_notice").prop("checked",false);
            $("#email_notice").prop("checked",false);
            $("#receive_div").hide();
            $("#is_sms").val(0);
            $(".yue").hide();
            $(".rate").hide();
            $('.payType li').removeClass('paySelect');
            $("#payId").val(0);
            $("#payType").val(1);
            $("#is_dk").val(0);
            $("#switchDk").val(0);
            $("#switchDk").prop("checked",false);
            $("#contact_html").html('');

            $(".coupon").hide();
            $("#coupon").val('');
            $(".coupon").hide();
            $("#coupon").val('');
            $("#activity").hide();
            $("#discount_tips").hide();
            $("#reach_tips").hide();
            $("#area_show").hide();
            toggle = false;
            layer.close(service);
            $("#service_info").hide();
            layui.form.render("checkbox");
            init();
        }

    });
    $('body').on('click','.toLogin',function(){

        let area = [];
        if($("#isMobile").val() == 1){
            area = ['90%', '90%'];
        }else {
            area =['380px', '800px'];
        }
        layer.open({
            type: 2,
            title: false,
            shadeClose: true,
            shade:0.5,
            zIndex:9999999999,
            area:area,
            content: ['/buyer', 'no']
        });

    });
    $(".vipInfo").mouseenter(function(){
        let html = $("#vipInfo").val();
        if(html != ''){
            var that = this;
            layer.tips(html, that,{tips: 3});
        }

    });
    layui.form.on('checkbox(sms_notice)', function(data){
        let s = data.elem.checked;
        if(s === true && $("#GoodsId").val() == 0){
            $("#is_sms").val(0);
            $("#sms_notice").prop("checked",false);
            layui.form.render("checkbox");
            layer.msg('请先选择商品');
            return false;
        }else if(s === true && $("#GoodsId").val() != 0){
            let sss = layer.confirm('出卡时，卡密码过长（大于200个字）将会导致接收的短信中无法显示卡密内容，请确认是否继续选择短信方式接收！',{title:'温馨提示'}, function(index){
                $("#email_notice").prop("checked",false);
                $("#receive_div").show();
                $("#sms_tip").show();
                $("#notice_title").html('手机号码:');
                $("#is_sms").val(1);
                layui.form.render("checkbox");
                layer.close(sss);
                calculation();
            },function(){
                $("#is_sms").val(0);
                $("#sms_notice").prop("checked",false);
                layui.form.render("checkbox");
                calculation();
            });

        }else {
            $("#receive_div").hide();
            $("#sms_tip").hide();
            $("#is_sms").val(0);
            calculation();
        }
    });

    layui.form.on('checkbox(email_notice)', function(data){
        let s = data.elem.checked;
        if(s === true && $("#GoodsId").val() == 0){
            $("#is_sms").val(0);
            $("#email_notice").prop("checked",false);
            layui.form.render("checkbox");
            layer.msg('请先选择商品');
            return false;
        }else if(s === true && $("#GoodsId").val() != 0){
            $("#sms_notice").prop("checked",false);
            $("#receive_div").show();
            $("#sms_tip").hide();
            $("#notice_title").html('邮箱地址:');
            $("#is_sms").val(2);
            calculation();
            layui.form.render("checkbox");
        }else {
            calculation();
            $("#sms_tip").hide();
            $("#is_sms").val(0);
            $("#receive_div").hide();
        }
    });
    // layui.form.on('switch(switchSms)', function(data){
    //     let s = data.elem.checked;
    //     if(s === true && $("#GoodsId").val() == 0){
    //         $("#is_sms").val(0);
    //         $("#switchSms").prop("checked",false);
    //         layui.form.render("checkbox");
    //         return layer.msg('请先选择商品');
    //     }else if(s === true && $("#GoodsId").val() != 0){
    //         let sss = layer.confirm('购卡数量过多或者出卡时卡密码过长将导致无法正常接收到短信！是否确认?', function(index){
    //             $("#is_sms").val(1);
    //             layer.close(sss);
    //             let mobile_input = $("input[name='contact[1]']");
    //
    //             if(mobile_input.length == 0){
    //
    //                 let html = '<div id="sms_contact" class="layui-form-item  additional ">   <div class="layui-inline " style="margin-top: 5px;">   <label class="layui-form-label required">手机号：</label>     <div class="layui-input-inline" style="width: 500px;">         <input type="text" data-key="1" name="contact[1]" autocomplete="off" placeholder="请输入相应预留信息" lay-verify="required" class="layui-input" style="border-radius: 5px;color: #555;">    </div>   </div>   </div>';
    //                 $('#contact_html').prepend(html);
    //             }
    //             calculation();
    //         },function(){
    //             $("#is_sms").val(0);
    //             $("#switchSms").prop("checked",false);
    //
    //              layui.form.render("checkbox");
    //         });
    //
    //     }else {
    //         $("#sms_contact").remove();
    //         $("#is_sms").val(0);
    //         calculation();
    //     }
    //
    // });
    layui.form.on('switch(switchDk)', function(data){
        let s = data.elem.checked;

        if(s === true){
            let ttt = $("#combination_pay_time").val();
            layer.confirm('选择余额抵扣后，对应抵扣金额会先行冻结，'+ttt+'分钟内未支付将解冻返回至余额，是否确认?', {icon: 3, title:'提示',closeBtn: 0}, function(index){
                layer.closeAll();
            },function () {
                $("#switchDk").val(0);
                $("#switchDk").prop("checked",false);
                $("#is_dk").val(0);
                layui.form.render("checkbox");
                calculation();
                layer.closeAll();
                return false;
            });
        }
        if(s === true && $("#GoodsId").val() == 0){
            $("#switchDk").val(0);
            $("#switchDk").prop("checked",false);
            $("#is_dk").val(0);
            layui.form.render("checkbox");
            return layer.msg('请先选择商品');
        }else if(s === true && $("#GoodsId").val() != 0){
            $("#switchDk").val(1);
            $("#is_dk").val(1);

            calculation();
        }else {
            $("#is_dk").val(0);
            $("#switchDk").val(0);
            calculation();
        }

    });
    layui.use('flow', function() {
        flow = layui.flow;
        init();
    });

    function init(){
        $('#LAY_demo1').remove();
        $('.desc').hide();
        $('.goods').prepend('<ul class="flow-default" id="LAY_demo1" style=""></ul>');
        page = 1;
        flow.load({
            elem: '#LAY_demo1' //流加载容器
            , scrollElem: '#LAY_demo1' //滚动条所在元素，一般不用填，此处只是演示需要。
            , done: function (page, next) { //执行下一页的回调

                goodsList(next);

            }
        });
    }

    $("#searchGoods").click(function () {
        // $("#cateId").val(0);
        // $('.cat ul li').removeClass('select');
        // $("#allGoods").addClass('select');
        $(".goodsName").html('尚未选择商品');
        $(".goodsInfo").html('未选中商品');
        $("#jiaose_box").hide();
        $('#quantity').removeAttr('disabled');
        $("#fee_payer").val(1);
        $("#GoodsId").val(0);
        $("#price").html(0);
        $("#kami_id").val('');
        $("#songNum").val(0);
        $("#is_xh").val(0);
        $("#goodsPrice").val(0);
        $("#xhPrice").val(0);
        $("#kucun").html(0);
        $("#vip_goods").val(0);
        $("#cards_stock_count").val(0);
        $("#card_password").hide();
        $(".smsPrice").html( $("#sms_payer").val());
        $("#sms_notice").prop("checked",false);
        $("#email_notice").prop("checked",false);
        $("#receive_div").hide();
        $("#is_sms").val(0);
        $(".yue").hide();
        $(".rate").hide();
        $('.payType li').removeClass('paySelect');
        $("#payId").val(0);

        $("#is_dk").val(0);
        $("#switchDk").val(0);
        $("#switchDk").prop("checked",false);
        $("#contact_html").html('');

        $(".coupon").hide();
        $("#coupon").val('');
        $(".coupon").hide();
        $("#coupon").val('');
        $("#coupon_type").val(1);
        $("#coupon_denomination").val(0);
        $("#activity").hide();
        $("#discount_tips").hide();
        $("#reach_tips").hide();
        $("#area_show").hide();
        toggle = false;
        layer.close(service);
        $("#service_info").hide();
        layui.form.render("checkbox");

        init();
    });
    document.onkeydown = function(e){
        var ev = document.all ? window.event : e;
        if(ev.keyCode==13) {
            $("#searchGoods").click();
        }
    };

    // function songStr() {
    //     let song = 0;
    //     let ddddd = 0;
    //     if($('#wholesale_discount').val() == 1){
    //
    //         for(var i in wholesale_discount_list){
    //             let num =  wholesale_discount_list[i]['num'];
    //
    //             let buynum =  Number($(".buyNum").val());
    //             if(buynum >= num){
    //                 song = 1;
    //                 $("#songNum").val(wholesale_discount_list[i]['price']);
    //             }
    //         }
    //     }
    //     if(song == 1){
    //          ddddd = Number($("#songNum").val());
    //     }
    //     if(ddddd > 0){
    //         $(".goodsInfo").html('('+'单价：'+$("#goodsPrice").val()+',数量:买'+ $(".buyNum").val()+'送'+ ddddd +',合计：'+ (ddddd+Number($(".buyNum").val())) +'张)');
    //     }else{
    //         $(".goodsInfo").html('('+'单价：'+$("#goodsPrice").val()+',数量:'+ $(".buyNum").val()+')');
    //     }
    //     calculation();
    // }
    function songStr() {
        let song = 0;
        let ddddd = 0;
        let yh = 0;
        let yh_price = 0;
        if($('#reach').val() == 1){
            $.each(reach_list, function(i, v){
                let need_buy =  i;
                let buynum =  Number($(".buyNum").val());
                if(buynum >= need_buy){
                    song = 1;
                    ddddd = Math.floor(buynum/need_buy);
                     ddddd =ddddd*v;
                }
                $("#songNum").val(ddddd);
            });
        }
        if($('#reach').val() == 2){
            $.each(reach_list, function(i, v){
                let need_buy =  v['buy'];
                let buynum =  Number($(".buyNum").val());
                if(buynum >= need_buy){
                    song = 1;
                    ddddd = v['num'];
                    $("#songNum").val(ddddd);
                }
            });
        }
        if($('#wholesale_discount').val() == 1){

            $.each(wholesale_discount_list, function(i, v){
                let need_buy =  v['num'];
                let buynum =  Number($(".buyNum").val());
                if(buynum >= need_buy){
                    $("#is_yh").val(1);
                    yh = 1;
                    $("#yh_price").val(v['price']);
                }
            });
        }
        if(ddddd > 0){
            if(yh == 1){
                $(".goodsInfo").html('('+'单价：'+$("#yh_price").val()+',数量:买'+ $(".buyNum").val()+'送'+ ddddd +',合计：'+ (ddddd+Number($(".buyNum").val())) +'张)');
            }else{
                $("#yh_price").val(0);
                $(".goodsInfo").html('('+'单价：'+$("#goodsPrice").val()+',数量:买'+ $(".buyNum").val()+'送'+ ddddd +',合计：'+ (ddddd+Number($(".buyNum").val())) +'张)');
            }
        }else{
            if(yh == 1){
                $(".goodsInfo").html('('+'单价：'+$("#yh_price").val()+',数量:'+ $(".buyNum").val()+')');
            }else{
                $("#yh_price").val(0);
                $(".goodsInfo").html('('+'单价：'+$("#goodsPrice").val()+',数量:'+ $(".buyNum").val()+')');
            }
        }

        calculation();
    }
    $("#coupon").blur(function (){
        let val = $("#coupon").val();

        if(val != ''){
            $.ajax({
                headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
                type: "POST",
                url: api_url+"/goods/checkcoupon",
                dataType: 'json',
                data: {coupon:val,'goods_id':$("#GoodsId").val(),'userid':$("#shopId").val(),'money':$("#totalPrice").val()},
                beforeSend: function(){
                    loading = layer.load();
                },
                error: function (request) {
                    layer.close(loading);
                    return    layer.msg("连接错误！");
                },

                success: function (res) {
                    layer.close(loading);
                    if (res.code === 0) {
                        $("#coupon_denomination").val(res.data.denomination);
                        $("#coupon_type").val(res.data.type);
                        calculation();
                    } else {
                        $("#coupon_denomination").val(0);
                        $("#coupon_type").val(1);
                        calculation();
                        return  layer.msg(res.msg);
                    }
                }
            });
        }else {
            $("#coupon_denomination").val(0);
            $("#coupon_type").val(1);
            calculation();
        }

    })
    function goodsList(next) {
        let shopId = $("#shopId").val();
        let cateId = $("#cateId").val();
        let agentId = $("#agentId").val();
        let goodsName = $("#goodsName").val();


        var lis = [];

        let data = {
            shopId:shopId,
            cateId:cateId,
            agentId:agentId,
            goodsName:goodsName,
            // ,
            page:page,
            limit:limit,
        };
        if($("#isDan").val() == 1){
            data['GoodsId'] = $("#GoodsId").val();
        }
        $.ajax({
            headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
            type: "POST",
            url: api_url+"/goods/getlist",
            dataType: 'json',
            data:data,
            beforeSend: function(){

                loading = layer.load();
            },
            error: function (request) {
                layer.close(loading);
                return    layer.msg("连接错误！");
            },

            success: function (res) {
                layer.close(loading);
                if (res.code === 0) {
                    let gData = res.data;
                    $("#goodsCount").html(gData.count);
                    let isMobile = $("#isMobile").val();
                    if(isMobile != 1){
                        //假设你的列表返回在data集合中
                        $.each(gData.data, function(index, item){
                            let html = ' <li data-id="'+ item.id +'">';
                            html += '  <p class="goods-name">'+ item.name+'</p>';
                            html += ' <i class="layui-icon layui-icon-circle" style="">';
                            html += '  </i>';


                            html += '  <p class="goods-price" style=""><span style="font-size: 20px;">￥</span>'+ item.price+'</p>';
                            html +='<div style="margin-top: 3px;">';

                            if(item.wholesale_discount == 1){
                                html += '<span  class="layui-badge layui-bg-orange liwu" style="font-size: 12px;">批</span>';
                            }
                            if(item.is_coupon == 1){
                                html += '<span  class="layui-badge layui-bg-red   liwu" style="font-size: 12px;">券</span>';
                            }
                            if(item.is_pick == 1){
                                html += '<span  class="layui-badge layui-bg-purple   liwu" style="font-size: 12px;">选</span>';
                            }
                            if(item.reach != 0){
                                html += '<span  class="layui-badge layui-bg-blue   liwu" style="font-size: 12px;">赠</span>';
                            }
                            if(item.vip_goods == 1){
                                html += '<span  class="layui-badge layui-bg-black   liwu" style="font-size: 12px;">折</span>';
                            }
                            if(item.cards_stock_str == '库存告罄'){
                                html += '  <span  style="color:#ff5722" class="stock" data-kucun="'+item.cards_stock_str+'">'+ item.cards_stock_str+'</span>';
                            }else if(item.cards_stock_str == '库存紧张'){
                                html += '  <span  style="" class="stock" data-kucun="'+item.cards_stock_str+'">'+ item.cards_stock_str+'</span>';
                            }else{
                                html += '  <span  style="color:#16baaa" class="stock" data-kucun="'+item.cards_stock_str+'">'+ item.cards_stock_str+'</span>';
                            }

                            html += ' </div>';
                            html += ' </li>';
                            lis.push(html);
                        });
                    }else {
                        //假设你的列表返回在data集合中
                        $.each(gData.data, function(index, item){
                            let html = ' <li data-id="'+ item.id +'">';
                            html += '  <p class="goods-name">'+ item.name+'</p>';


                            html += '  <p class="goods-price" style=""><span style="font-size: 12px;">￥</span>'+ item.price ;

                            if(item.cards_stock_str == '库存告罄'){
                                html += '  <span  style="color:#ff5722" class="stock" data-kucun="'+item.cards_stock_str+'">'+ item.cards_stock_str+'</span>';
                            }else if(item.cards_stock_str == '库存紧张'){
                                html += '  <span  style="" class="stock" data-kucun="'+item.cards_stock_str+'">'+ item.cards_stock_str+'</span>';
                            }else{
                                html += '  <span  style="color:#16baaa" class="stock" data-kucun="'+item.cards_stock_str+'">'+ item.cards_stock_str+'</span>';
                            }
                            html += ' </p>';

                            html += ' </li>';
                            lis.push(html);
                        });
                    }

                    page = gData.next_page;
                    //执行下一页渲染，第二参数为：满足“加载更多”的条件，即后面仍有分页
                    //pages为Ajax返回的总页数，只有当前页小于总页数的情况下，才会继续出现加载更多
                    next(lis.join(''), page < gData.all_page+1);
                    if(gData.is_choose == 1){
                        $(".flow-default li:first").click();

                    }
                } else {
                    return  layer.msg(res.msg);
                }
            }
        });
    };
    $('body').on('click','.goods ul li',function(){

        if( !$(this).hasClass('select')){
            let that = $(this);
            let id = $(this).attr('data-id');
            let shopId = $("#shopId").val();
            $.ajax({
                headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
                type: "POST",
                url: api_url+"/goods/getinfo",
                dataType: 'json',
                data:{
                    shopId:shopId,
                    id:id,
                },
                beforeSend: function(){
                    loading = layer.load();
                },
                error: function (request) {
                    layer.close(loading);
                    return    layer.msg("连接错误！");
                },
                success: function (res) {
                    layer.close(loading);
                    if (res.code === 0) {
                        $("#jiaose_box").hide();
                        $("#account_list").html('');
                        $("#contact_html").html('');

                        $(".coupon").hide();
                        $("#coupon").val('');
                        $("#activity").hide();
                        $("#discount_tips").hide();
                        $("#reach_tips").hide();
                        $(".coupon").hide();
                        $("#coupon").val('');
                        $("#coupon_type").val(1);
                        $("#coupon_denomination").val(0);
                        let gData = res.data;
                        $("#GoodsId").val(id);
                        $('.goods ul li').removeClass('select');
                        $('.goods ul li').find('i').removeClass('layui-icon-ok-circle');
                        $('.goods ul li').find('i').addClass('layui-icon-find-fill');
                        $('#quantity').removeAttr('disabled');
                        that.addClass('select');
                        that.find('i').removeClass('layui-icon-find-fill');
                        that.find('i').addClass('layui-icon-ok-circle');
                        $("#songNum").val(0);
                        if(gData.is_login == 1){
                            $(".toLogin").click();
                        }
                        $("#is_login").val(gData.is_login);
                        $("#fee_payer").val(gData.fee_payer);
                        $("#vip_goods").val(gData.vip_goods);
                        $(".desc").show();
                        $("#goodsContent").html(gData.content);
                        $(".goodsName").html(gData.name);
                        $(".yue").hide();
                        $(".rate").hide();
                        $('.payType li').removeClass('paySelect');
                        $("#payId").val(0);
                        that.find('.stock').html(gData.cards_stock_str);
                        $("#kucun").html(gData.cards_stock_str);

                        $("#wholesale_discount").val(gData.wholesale_discount);
                        wholesale_discount_list = gData.wholesale_list;
                        if(wholesale_discount_list &&   Object.keys(wholesale_discount_list).length > 0){
                            $("#activity").show();
                            var str1 ='';
                            $.each(wholesale_discount_list, function(i, v){
                                str1 +='买满：'+ v.num +'张,单价优惠为：'+ v.price+'元。<br>';
                            });
                            $("#discount_tips").show();
                            $("#discount_tips_str").html(str1);

                        }

                        $("#reach").val(gData.reach);
                        reach_list = gData.reach_list;
                        if(gData.reach == 2 &&   Object.keys(reach_list).length > 0){
                            $("#activity").show();
                            var str2 ='';
                            $.each(reach_list, function(i, v){
                                str2 +='买满：'+ v.buy +'张,送：'+ v.num+'张。<br>';
                            });
                            $("#reach_tips").show();
                            $("#reach_tips_str").html(str2);
                        }
                        if(gData.reach == 1 &&   Object.keys(reach_list).length > 0){
                            $("#activity").show();
                            var str3 ='';
                            $.each(reach_list, function(i, v){
                                str3 +='每买：'+ i +'张,额外送：'+ v +'张。<br>';
                            });
                            $("#reach_tips").show();
                            $("#reach_tips_str").html(str3);

                        }
                        contact_limit = gData.contact_limit;
                        if(contact_limit &&   Object.keys(contact_limit).length > 0){
                            var html = '<fieldset class="layui-elem-field layui-field-title" style="">\n' +
                                '            <legend>预留信息</legend>\n' +
                                '        </fieldset>' ;
                            $.each(contact_limit, function(i, v){
                                html += '   <div class="layui-form-item  additional " >' ;
                                html += '   <div class="layui-inline " style="margin-top: 5px;" >' ;
                                html += '   <label class="layui-form-label required">'+ v.title +'：</label>' ;
                                html += '     <div class="layui-input-inline" style="width: 500px;">' ;
                                html += '         <input type="text" lay-verify="required" data-key="'+v.type  +'" name="contact[]"  autocomplete="off" placeholder="请输入相应预留信息" class="layui-input" style="border-radius: 5px;color: #555;">' ;
                                html += '    </div>   </div>   </div>' ;
                            });

                            html +=   '</tbody></table>';

                            $("#contact_html").html(html);
                        }
                        $(".smsPrice").html(gData.smsPrice);
                        if(gData.is_coupon == 1){

                            $(".coupon").show();
                        }
                        if(gData.take_card_type == 0){
                            $("#card_password").hide();
                        }else if(gData.take_card_type == 1){
                            $("#take_card_password").attr('placeholder','输入您的取卡密码(请自行定义) 必填');
                            $("#card_password").show();
                        }else{
                            $("#take_card_password").attr('placeholder','输入您的取卡密码(请自行定义) 选填');
                            $("#card_password").show();
                        }
                        $("#take_card_type").val(gData.take_card_type);

                        if(gData.visit_type == 1){
                            visit_password();
                        }
                        ka_page = 1;
                        ka_is_page = true;
                        $("#kami_id").val('');
                        $("#start_nums").val(0);
                        $("#goodsPrice").val(gData.price);
                        $("#xh_price").html(gData.pick_price);
                        $("#sms_payer").val(gData.sms_payer);
                        $("#sms_notice").prop("checked",false);
                        $("#email_notice").prop("checked",false);
                        $("#receive_div").hide();
                        $("#is_sms").val(0);
                        $("#is_dk").val(0);
                        $("#switchDk").val(0);
                        $("#switchDk").prop("checked",false);

                        let added_services = $("#added_services").val();
                        if(added_services == 1){
                            $("#sms_notice").prop("checked",true);
                            $("#email_notice").prop("checked",false);
                            $("#receive_div").show();
                            $("#sms_tip").show();
                            $("#notice_title").html('手机号码:');
                            $("#is_sms").val(1);
                        }
                        if(added_services == 2){
                            $("#email_notice").prop("checked",true);
                            $("#sms_notice").prop("checked",false);
                            $("#receive_div").show();
                            $("#sms_tip").hide();
                            $("#notice_title").html('邮箱地址:');
                            $("#is_sms").val(2);
                        }
                        layui.form.render("checkbox");
                        if(gData.limits_min == 0){
                            $(".buyNum").val(1);
                            $("#limits_min").val(1);
                        }else {
                            $(".buyNum").val(gData.limits_min);
                            $("#limits_min").val(gData.limits_min);
                        }
                        if(gData.limits_max == 0){
                            $("#limits_max").val(999999);

                        }else {
                            $("#limits_max").val(gData.limits_max);
                        }
                        $("#cards_stock_count").val(gData.stock);
                        if(gData.stock <  $("#limits_max").val()){
                            $("#limits_max").val(gData.stock);
                        }

                        songStr();
                        if(gData.is_pick == 1){
                            $("#xhPrice").val(gData.pick_price);
                            $("#is_xh").val(1);
                            $("#jiaose_box").show();
                            getAccount(id,'');
                        }else {
                            $("#is_xh").val(0);
                            $("#xhPrice").val(0);
                            $("#selectAccount").hide();
                            $("#jiaose_box").hide();
                        }
                        get_rate(shopId,id);

                        //客服ID
                        layer.close(service);
                        $("#service_info").hide();
                        if(gData.is_service === true){
                            $("#service_info").show();
                            $("#shop_chats").attr('data-src','/service_info?id=' + +encodeURIComponent(gData.service_id));
                        }else {
                            $("#service_info").hide();
                            $("#shop_chats").attr('data-src','');
                        }

                        //合区展示

                        if(gData.pick_area_show === true){
                            $("#area_show").show();
                            toggle = true;

                        }
                    } else {
                        return  layer.msg(res.msg);
                    }
                }
            });
        }

    });


    function get_rate(shopId,goods_id){
        $.ajax({
            headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
            type: "POST",
            url: api_url+"/goods/getrate",
            dataType: 'json',
            data:{
                userid: shopId,
                goods_id:goods_id,
                isMobile : $("#isMobile").val()
            },
            beforeSend: function(){
                loading = layer.load();
            },
            error: function (request) {
                layer.close(loading);
                return    layer.msg("连接错误！");
            },
            success: function (rel) {
                layer.close(loading);
                if(rel.code === 0){
                    let data = rel.data;
                    let html = '';
                    $.each(data, function(i, v){
                        html +='<li data-id="'+ v.channel_id +'" data-type="'+ v.channel_type +'" data-ident="'+ v.ident +'" data-rate="'+ v.rate +'" data-fee="'+ v.min_fee +'" style="'+ v.style +'"  ><img style="height:40px;" src="'+ v.image +'"></li>';

                    });
                    $(".payType").html(html);
                }else {
                    layer.msg(rel.msg);
                    return false;
                }
            }
        });
    }
    function visit_password(){

        let area = [];
        if($("#isMobile").val() == 1){
            area = ['90%', '90%'];
        }else {
            area =['500px', '200px'];
        }
        let html = ' <div class="layui-form-item" style="margin-top: 40px;padding-right:20px;">\n' +
            '        <label class="layui-form-label">购买密码:</label>\n' +
            '        <div class="layui-input-block">\n' +
            '            <input type="text" id="visit_password_ver"  placeholder="输入购买密码" class="layui-input" style="border-radius: 5px;color: #555;max-width: 100%;">\n' +
            '        </div>\n' +
            '    </div>';
        let ssss = layer.open({
            type: 1,
            skin:'layui-layer-molv',
            shadeClose: false,
            // closeBtn : false,
            anim: 2,
            zIndex:9999999999,
            content: html,
            area: area,
            title: '购买密码确认',
            btn: ['立即验证'],
            yes:function () {

                let visit_password_ver = $("#visit_password_ver").val();
                if(!visit_password_ver){
                    layer.msg('请输入购买密码');
                    return false;
                }
                let GoodsId = $("#GoodsId").val();
                $("#visit_password").val(visit_password_ver);
                let loading;
                $.ajax({
                    headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
                    type: "POST",
                    url: api_url+"/goods/visitpassword",
                    dataType: 'json',
                    data:{
                        password: visit_password_ver,
                        goods_id: GoodsId,
                    },
                    beforeSend: function(){
                        loading = layer.load();
                    },
                    error: function (request) {
                        layer.close(loading);
                        return    layer.msg("连接错误！");
                    },
                    success: function (rel) {
                        layer.close(loading);
                        if(rel.code === 0){
                            layer.msg(rel.msg,{time:1000},function (){
                                $("#visit_password").val(visit_password_ver);
                                layer.close(ssss);
                            });
                        }else {
                            layer.msg(rel.msg);
                            return false;
                        }
                    }
                });
            },
        });
    }
    $('#discount_tips').hover( function(){
        layer.tips($("#discount_tips_str").html(), '#discount_tips',{ tips: 1});
    });
    $('#reach_tips').hover( function(){
        layer.tips($("#reach_tips_str").html(), '#reach_tips',{ tips: 1});
    });


    $('body').on('click','#toPay',function() {
        let GoodsId = Number($("#GoodsId").val());
        let quantity = Number($("#quantity").val());
        let is_sms = Number($("#is_sms").val());
        let sms_receive = $("#sms_receive").val();
        let take_card_type = $("#take_card_type").val();
        let take_card_password = $("#take_card_password").val() || '';
        let payId = $("#payId").val();
        let payType = $("#payType").val();
        if(!GoodsId ||  GoodsId == 0){
            layer.msg('请先选择商品');
            return false;
        }
        if(payId <= 0){
            layer.msg('请选择支付方式！');
            return false;
        }
        var isValid =  layui.form.validate('.PayContent');  // 主动触发验证，v2.7.0 新增
        if(!isValid){
            return  false;
        }
        if(is_sms == 1){
            let myreg = /^1[3|4|5|6|7|8|9][0-9]{9}$/;
            let is = myreg.test(sms_receive);
            if(!is){
                layer.msg('开启短信服务后，请输入正确的手机号码！');
                return false;
            }
        }
        if(is_sms == 2) {
            let myreg = /^\w+([._-]\w+)*@(\w+\.)+\w+$/;
            let is = myreg.test(sms_receive);
            if(!is){
                layer.msg('开启邮箱服务后，请输入正确的邮箱地址！');
                return false;
            }
        }
        if(take_card_type == 1 && take_card_password == ''){
            layer.msg('请输入你的取卡密码！');
            return false;
        }
        //是否登陆
        if($("#is_login").val() == 1 && $("#member_id").val() <= 0){
            $(".toLogin").click();
        }else {
            var returna_date = $("input[name^='contact']");
            var contact = [];
            for(var x=0; x<returna_date.length;x++){
                contact.push($(returna_date[x]).val());
            }
            $.ajax({
                type: "POST",
                headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
                url: api_url+"/goods/createorder",
                dataType: 'json',
                data:{
                    GoodsId: GoodsId,
                    quantity:quantity,
                    shopId:$("#shopId").val(),
                    is_sms:is_sms,
                    sms_receive:sms_receive,
                    contact:contact,
                    take_card_password:take_card_password,
                    payId:payId,
                    payType:payType,
                    coupon : $("#coupon").val(),
                    is_xh:$("#is_xh").val(),
                    kami_id:$("#kami_id").val(),
                    is_dk:$("#is_dk").val(),
                    visit_password:$("#visit_password").val(),
                },
                beforeSend: function(){
                    loading = layer.load();
                },
                error: function (request) {
                    layer.close(loading);
                    return    layer.msg("连接错误！");
                },
                success: function (rel) {
                    layer.close(loading);
                    if(rel.code === 0){
                        let html = rel.data.url;
                        let area = [];
                        if($("#isMobile").val() == 1){
                            area = ['90%', '90%'];
                        }else {
                            area =['600px', '700px'];
                        }
                        let ssss = layer.open({
                            type: 2,
                            skin:'pay-title-class',
                            shadeClose: false,
                            closeBtn : false,
                            anim: 2,
                            zIndex:9999999999,
                            content: html,
                            area: area,
                            title: '订单确认',
                            btn: ['确认付款','重新选择'],
                            yes:function (index,layero) {
                                // 父页面获取子页面的iframe
                                var body = layer.getChildFrame('body', index);
                                body.find('button[type="submit"]').trigger('click');
                                return false;
                            },
                        });
                    }else {
                        layer.msg(rel.msg);
                    }
                }
            });
        }

    });
    // 选号账号
    $('body').on('click','#getS',function() {
        if (ka_page > 1) {
            ka_page -= 1;
            let pick_account = $("#pick_account").val();
            getAccount($("#GoodsId").val(),pick_account);
            $("#kami_id").val('');
            $("#start_nums").val(0);
            $("#kami_info").hide();
            $('#quantity').removeAttr('disabled');
            $("#quantity").val($("#limits_min").val());
            songStr();

        }else {
            layer.msg('没有更多了');
        }
    });
    $('body').on('click','#getE',function(){
        if(ka_is_page){
            ka_page +=1;
            let pick_account = $("#pick_account").val();
            getAccount($("#GoodsId").val(),pick_account);
            $("#kami_id").val('');
            $("#start_nums").val(0);
            $('#quantity').removeAttr('disabled');
            $("#quantity").val($("#limits_min").val());
            songStr();
        }else{
            layer.msg('没有更多了');
        }
        $("#kami_info").hide();

    });
    $('body').on('click','#pick_search',function(){
        let pick_account = $("#pick_account").val();

        ka_is_page = true;
        ka_page = 1;
        getAccount($("#GoodsId").val(),pick_account);
        $("#kami_id").val('');
        $("#start_nums").val(0);
        $("#quantity").val($("#limits_min").val());
        $('#quantity').removeAttr('disabled');
        songStr();
        $("#kami_info").hide();
    });
    function getAccount(goodid,pick_account=''){
        let loading;
        $.ajax({
            headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
            type: "POST",
            url: api_url+"/goods/picklist",
            dataType: 'json',
            data:{
                goodsid: goodid,
                pick_account:pick_account,
                page:ka_page,
                userid:$("#shopId").val(),
                type:'new'
            },
            beforeSend: function(){
                loading = layer.load();
            },
            error: function (request) {
                layer.close(loading);
                return    layer.msg("连接错误！");
            },
            success: function (rel) {
                layer.close(loading);
                if(rel.code === 0){
                    let data = rel.data;
                    let html = '';
                    if(data.length <= 0){
                        ka_is_page = false;
                    }else{
                        ka_is_page =true;
                        if(data.length < 10){
                            ka_is_page = false;
                        }
                        $("#jiaose_box").show();
                        if(rel.count > 10){
                            $("#selectAccount").show();
                        }

                        html = '<table class="goodscards">';
                        html += '<tbody><tr><td style=" font-size: 14px;font-weight: 600; padding: 5px;">昵称</td><td style=" font-size: 14px;font-weight: 600; padding: 5px;">其他</td></tr>';
                        for (var i=0;i<data.length;i++){
                            html +='<tr><td style="width: 25%; cursor: pointer; padding: 5px; " class="copyBtn getDetailInfo" data-clipboard-text="'+ data[i].content[0] +'" id="jst_'+data[i].id +'" data-id="'+data[i].id +'">'+ data[i].content[0] +'</td>';
                            html +='<td style="padding: 5px; ">'+data[i].content[1]+'</td></tr>';
                        }
                        html += '</tbody></table>'
                    }

                    $('#account_list').html(html);
                    $('#account_list').show();
                }
            }
        });

    }
    $('body').on('click','#jian',function(){
        let ds =  $('#quantity').attr('disabled');
        if(ds){
            return layer.msg('自由选号时不能编辑购买数量');
        }
        num(1);
    });
    $('body').on('click','#jia',function(){
        let ds =  $('#quantity').attr('disabled');
        if(ds){
            return layer.msg('自由选号时不能编辑购买数量');
        }
        num(2);
    });
    $("#quantity").off('blur').on('blur', function(){
        num(3);
    });

    function num(type){

        let quantity = $("#quantity").val();
        quantity = Number(quantity);
        if(type == 1){
            quantity -= 1;
        }else if (type == 2) {
            quantity += 1;
        }
        let goodsId= $("#GoodsId").val();
        if(goodsId <= 0){
            $("#quantity").val(1);
            $("#songNum").val(0);
            return layer.msg('请先选择商品');
        }
        let min  =   Number($("#limits_min").val());
        let max =   Number($("#limits_max").val());
        let cards_stock_count =   Number($("#cards_stock_count").val());


        // if(quantity > cards_stock_count){
        //
        //     if(max > cards_stock_count){
        //         $("#quantity").val(cards_stock_count);
        //     }else {
        //         $("#quantity").val(max);
        //     }
        //     songStr();
        //     // return layer.msg('库存数量不足！');
        // }
        if(quantity < min){
            $("#quantity").val(min);
            songStr();

            return layer.msg('最少购买：'+min+'张');
        }else if(quantity > max){
            $("#quantity").val(max);
            songStr();
            return layer.msg('最多购买：'+max+'张');
        }
        $("#quantity").val(quantity);
        songStr();
    };
    $('body').on('click','.getDetailInfo',function(){
        let id = $(this).attr('data-id');

        let loading;
        $.ajax({
            headers: {'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')},
            type: "POST",
            url: api_url+"/goods/accountinfo",
            dataType: 'json',
            data:{id: id,userid:$("#shopId").val()},
            beforeSend: function(){
                loading = layer.load();
            },
            error: function (request) {
                layer.close(loading);
                layer.msg("连接错误！");
                return false;
            },
            success: function (rel) {
                layer.close(loading);
                if(rel.code === 0){
                    let start =  $('.act').length;
                    if($('#jst_'+id).hasClass('act')){
                        $('#jst_'+id).removeClass('act');
                        start -=1;
                        if(start <1) {
                            $("input[name='quantity']").val(1);
                        }else {
                            $("input[name='quantity']").val(start);
                        }

                        $("#kami_info").hide();
                        let  str= ','+id;
                        let strs= $("#kami_id").val();

                        strss=strs.replace(str,'');

                        $("#kami_id").val(strss);

                    }else{
                        //战绩查询
                        if(rel.data.lol_query == true){
                            lol_query(id,$("#shopId").val());
                        }
                        start +=1;
                        if(start > 1){
                            $("input[name='quantity']").val(start);
                        }else{
                            $("input[name='quantity']").val(1);
                        }
                        let r = num(3);
                        if(typeof(r) == "undefined"){
                            $('#jst_'+id).addClass('act');
                            $("#kami_id").val($("#kami_id").val()+','+id);
                        }
                    }
                    start =  $('.act').length;
                    if(start > 0){
                        $('#quantity').attr('disabled','disabled');
                    }else {
                        $('#quantity').removeAttr('disabled');
                    }
                    $('#start_nums').val(start);
                    calculation();


                }else{
                    layer.msg('账号信息不存在');
                    return false;
                }
            }
        });

    });
    let swsw ;
    function lol_query(id,user_id){
        let area = [];
        let title = '实时数据查询';
        if($("#isMobile").val() == 1){
            title = '点击按钮查看账号数据';
            area = ['100%', '45px'];
        }else {
            let width =  $(document.body).width()*0.15;

            if(width < 300){
                width = 300;
            }
            if(width > 400){
                width = 400;
            }
            area =[width+'px', '750px'];
        }
        layer.close(swsw);
        swsw = layer.open({
            type: 2,
            skin:'layui-layer-molv',
            shadeClose: false,
            shade: 0,
            resize:true,
            offset: 'lb',
            closeBtn : true,
            maxmin:true,
            anim: 4,
            // zIndex:9999999999,
            content:  api_url+"/lolquery/index?id="+id+'&userid='+encodeURIComponent(user_id),
            area: area,
            title: title,
            btn: false,
        });
    };
    $("#notice").click(function () {
        let area = [];
        if($("#isMobile").val() == 1){
            area = ['90%', '90%'];
        }else {
            area =['800px', '90%'];
        }
        let sss = layer.open({
            type: 1,
            skin:'layui-layer-molv',
            shadeClose: true,
            closeBtn : false,
            anim: 4,
            zIndex:9999999999,
            content: '<div style="padding: 10px 20px;">'+ $("#shop_notice").val() +'</div>',
            area: area,
            title: '商家公告',
            btn: ['已阅'],
            yes:function () {
                Set('notice',1,3600*2*1000);
                layer.close(sss);
            }

        });
    });
    if($("#auto_notice").val() == 1){
        if(Get('notice') !== 1){
            $("#notice").click();
        }
    }
    let timer;  let protocol_time;
    if( Get('buy_protocol')== 1){
        protocol_time = 0;
    }else{
        protocol_time =  $("#protocol_second").val();
    }


    layui.util.on('lay-on', {

        photots: function(){
            let img = $(this).attr('src');
            let data = [ {
                "alt": "商品说明",
                "pid": 1,
                "src": img,
            }];
            layer.photos({
                photos: {
                    "title": false,
                    "start": 0,
                    "data": data
                }
            });
        },
        "test-count-down": function () {
            let area = [];
            if($("#isMobile").val() == 1){
                area = ['90%', '90%'];
            }else {
                area =['800px', '90%'];
            }
            let sss = layer.open({
                type: 1,
                skin:'layui-layer-molv',
                closeBtn : false,
                shadeClose: false,
                anim: 4,
                zIndex:9999999999,
                content: '<div style="padding: 10px 20px;">'+ $("#buy_protocol").val() +'</div>',
                area: area,
                title: '购卡协议',
                btn: ['已阅'],
                success: function (layero, index) {
                    var setText = function (start) {
                        let btn = $("#layui-layer"+index).find('.layui-layer-btn0');
                        btn.addClass('layui-bg-gray');
                        btn.html('阅读倒计时：<span class="layui-font-red">' + (start ? protocol_time :--protocol_time) + '</span> 秒');
                        if (protocol_time <= 0){
                            clearInterval(timer);
                            btn.removeClass('layui-bg-gray');
                            $("#layui-layer"+index).find('.layui-layer-btn0').html('已阅');
                        }

                    };
                    setText(true)
                    timer = setInterval(setText, 1000);
                },

                yes:function () {
                    if(protocol_time > 0){
                        return false;
                    }
                    Set('buy_protocol',1,3600*2*1000);
                    layer.close(sss);
                }

            });
        }
    });

    if($("#auto_protocol").val() == 1){
        if(Get('buy_protocol') !== 1){
            $("#protocol").click();
        }
    }
    function calculation() {

        let goodsPrice = Number($("#goodsPrice").val());
        let yh_price = Number($("#yh_price").val());
        let quantity = Number($("#quantity").val());
        let smsPrice = Number($("#smsPrice").val());
        let sms_payer = $("#sms_payer").val();
        let is_sms = $("#is_sms").val();
        let is_xh = $("#is_xh").val();
        let vip_goods = $("#vip_goods").val();
        let vip_discount = $("#vip_discount").val();
        let start_nums = Number($("#start_nums").val());
        let xhPrice = Number($("#xhPrice").val());
        let price ;
        if(yh_price > 0){
            price =yh_price*quantity;
        }else{
            price =goodsPrice*quantity;
        }
        if(vip_goods != 0 && vip_discount){
            price =   parseFloat( vip_discount/100*price).toFixed(2);
        }
        if(is_xh == 1 && start_nums> 0){ //不抵扣显示的价格
            price = price*1 + parseFloat( start_nums*xhPrice).toFixed(2)*1 ;
        }
        price =  parseFloat(price).toFixed(2);
        //优惠券
        let coupon_denomination = $("#coupon_denomination").val();
        let coupon_money = 0;
        if(coupon_denomination > 0){
            let coupon_type = $("#coupon_type").val();
            if(coupon_type == 1){
                coupon_money = coupon_denomination;
            }else{
                coupon_money = Number(coupon_denomination/100*price).toFixed(2)
            }
        }
        price = (price-coupon_money).toFixed(2);
        if(price < 0) price = 0;
        $("#totalPrice").val(price);
        let fee_payer = $("#fee_payer").val();
        if(fee_payer == 2){
            let paySelect = $(".payType").find('.paySelect');

            if(paySelect.length){
                let rate = Number($(".paySelect").attr('data-rate'));
                let min = Number($(".paySelect").attr('data-fee')).toFixed(2);

                let rate_fee = (rate/1000*Number($("#totalPrice").val()) || 0).toFixed(2) ;

                if(rate_fee < min){
                    $("#rate_fee").val(min);
                }else{
                    $("#rate_fee").val(rate_fee);
                }
            }else {
                $("#rate_fee").val(0);
            }

        }else {
            $("#rate_fee").val(0);
        }

        let sms_price = 0;
        if(sms_payer == 1 && is_sms == 1){
            sms_price = smsPrice;
        }else {
            sms_price = 0;
        }
        let total = (Number($("#totalPrice").val())+Number($("#rate_fee").val())+sms_price);
        total = total.toFixed(2);
        if(Number($("#is_dk").val()) == 1){

            let ddd = Number($("#umoney").val()) > total  ?  total : Number($("#umoney").val());
            ddd =  parseFloat(ddd).toFixed(2);
            // if(Number($("#rate_fee").val()) > 0 && (Number($("#rate_fee").val()) <=  Number($("#umoney").val()))){
            //     $(".dkPrice").html(ddd+'<span style="font-size: 12px;color: #515151;line-height: 12px;">（含手续费：'+ $("#rate_fee").val() +'）</span>');
            // }else {
            //     $(".dkPrice").html(ddd);
            // }
            $(".dkPrice").html(ddd);
            $("#dkPrice").val(ddd);

        }else {

            let ddd = Number($("#umoney").val()) > total ?  total : Number($("#umoney").val());
            ddd =  parseFloat(ddd).toFixed(2);
            $("#dkPrice").val(0);
            $(".dkPrice").html(ddd);

        }
        if(Number($("#rate_fee").val()) > 0){
            $("#fee_str").show();
            $("#fee").html($("#rate_fee").val());
        }else {
            $("#fee_str").hide();
        }
        if(Number($("#dkPrice").val()) > 0){
            let dd = total-Number($("#dkPrice").val());
            dd = dd.toFixed(2);
            $("#price").html(dd);
        }else {
            $("#price").html(Number(total).toFixed(2));
        }


    }
    // 存储
    function Set(key,value,sTime){
        let obj = {
            data: value,
            time: Date.now(),
            storageTime: sTime
        }
        window.localStorage.setItem(key, JSON.stringify(obj))
    }

    // 取值
    function Get(key){
        let obj = window.localStorage.getItem(key);
        if(!obj){
            return  false;
        }
        obj = JSON.parse(obj);
        if(Date.now()-obj.time>obj.storageTime){
            window.localStorage.removeItem(key);
            return null
        }
        return obj.data
    }

    var clipboard = new ClipboardJS('.copyBtn');
    clipboard.on('success', function(e) {
        e.clearSelection();
    });

    $(document).on('click', '#collapsed', function() {
        if(toggle == true){
            toggle = false;
            $("#regionTable").attr('style','width:60px;')
            $("#tableContent").hide();
            $("#anniu").hide();
            $("#expandIcon").hide();
            $("#collapsed").addClass('collapsed');
        }else {
            toggle = true;
            $("#regionTable").attr('style','width:290px;')
            $("#tableContent").show();
            $("#anniu").show();
            $("#expandIcon").show();
            $("#collapsed").removeClass('collapsed');
        }
    });

});
